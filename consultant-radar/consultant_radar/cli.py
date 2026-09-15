from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .digest import render_digest
from .match import Filters, classify
from .models import Job
from .sources import build_registry
from .store import Store

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _companies(config_path: Path, company_id: str | None = None) -> list[dict[str, Any]]:
    payload = _load_json(config_path)
    companies = [c for c in payload.get("companies") or [] if c.get("enabled", True)]
    if company_id:
        companies = [c for c in companies if c["id"] == company_id]
        if not companies:
            raise SystemExit(f"Company not found or disabled: {company_id}")
    return companies


def cmd_companies(args: argparse.Namespace) -> int:
    for company in _companies(args.companies):
        print(f"{company['id']:16} {company['source']:12} {company['name']}")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    companies = _companies(args.companies, args.company)
    filters = Filters.load(args.filters)
    store = Store(args.db)
    registry = build_registry()
    scan_id = store.start_scan()
    seen_total = 0
    matched_rows: list[tuple[Job, list[str]]] = []
    errors: list[str] = []
    stats = {"seen": 0, "new": 0}
    try:
        for company in companies:
            source_name = company["source"]
            source = registry.get(source_name)
            if source is None:
                errors.append(f"{company['id']}: unknown source {source_name}")
                continue
            try:
                jobs = source.fetch(company)
            except Exception as exc:  # noqa: BLE001 — isolate one board failure
                errors.append(f"{company['id']}: {type(exc).__name__}: {exc}")
                continue
            seen_total += len(jobs)
            kept = classify(jobs, filters, require_include=not args.all)
            matched_rows.extend(kept)
            print(
                f"{company['id']}: fetched {len(jobs)}, matched {len(kept)}",
                file=sys.stderr,
            )
        stats = store.upsert_jobs(scan_id, matched_rows)
        store.finish_scan(
            scan_id,
            seen=seen_total,
            matched=len(matched_rows),
            new=stats["new"],
        )
    finally:
        listed = store.list_jobs(
            company_id=args.company,
            only_new=not args.all_seen,
            scan_id=scan_id,
            limit=args.limit,
        )
        store.close()

    if args.json:
        json.dump(
            {
                "scan_id": scan_id,
                "seen": seen_total,
                "matched": len(matched_rows),
                "new": stats["new"],
                "errors": errors,
                "jobs": listed,
            },
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        print(
            f"scan {scan_id}: seen={seen_total} matched={len(matched_rows)} "
            f"new={stats['new']}"
        )
        if errors:
            print("errors:")
            for err in errors:
                print(f"  - {err}")
        sys.stdout.write(render_digest(listed, title="Consultant Radar — nuevas"))
    return 1 if errors and not listed else 0


def cmd_list(args: argparse.Namespace) -> int:
    store = Store(args.db)
    try:
        rows = store.list_jobs(
            company_id=args.company,
            only_new=args.new,
            limit=args.limit,
        )
    finally:
        store.close()
    if args.json:
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_digest(rows, title="Consultant Radar — listado"))
    return 0


def cmd_digest(args: argparse.Namespace) -> int:
    store = Store(args.db)
    try:
        rows = store.list_jobs(
            company_id=args.company,
            only_new=args.new,
            limit=args.limit,
        )
    finally:
        store.close()
    text = render_digest(rows)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out} ({len(rows)} jobs)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="consultant-radar",
        description="Detecta ofertas de consultoras (Accenture Song, Deloitte, KPMG, ...).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--companies",
        type=Path,
        default=ROOT / "config" / "companies.json",
        help="JSON de empresas y fuentes ATS",
    )
    parser.add_argument(
        "--filters",
        type=Path,
        default=ROOT / "config" / "filters.json",
        help="JSON de keywords include/exclude",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT / "data" / "radar.sqlite",
        help="SQLite de ofertas vistas",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_companies = sub.add_parser("companies", help="Lista empresas configuradas")
    p_companies.set_defaults(func=cmd_companies)

    p_scan = sub.add_parser("scan", help="Escanea fuentes ATS y guarda novedades")
    p_scan.add_argument("--company", help="Solo esta company id")
    p_scan.add_argument("--limit", type=int, default=80, help="Máximo de filas a imprimir")
    p_scan.add_argument("--json", action="store_true")
    p_scan.add_argument(
        "--all",
        action="store_true",
        help="No exigir keyword include (sigue aplicando excludes)",
    )
    p_scan.add_argument(
        "--all-seen",
        action="store_true",
        help="Imprimir también ofertas ya vistas, no solo las nuevas del scan",
    )
    p_scan.set_defaults(func=cmd_scan)

    p_list = sub.add_parser("list", help="Lista ofertas guardadas")
    p_list.add_argument("--company")
    p_list.add_argument("--limit", type=int, default=80)
    p_list.add_argument("--new", action="store_true", help="Solo first_seen = last_seen")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_digest = sub.add_parser("digest", help="Escribe un markdown con el listado")
    p_digest.add_argument("--company")
    p_digest.add_argument("--limit", type=int, default=80)
    p_digest.add_argument("--new", action="store_true")
    p_digest.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "digest.md",
    )
    p_digest.set_defaults(func=cmd_digest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
