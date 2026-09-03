"""CLI: queries | discover | ensure-schema | sync."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import CdeConfig, ROOT
from .unipile_search import discover, search_body, resolve_ids


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def cmd_queries(cfg: CdeConfig) -> int:
    locations = resolve_ids(cfg, ptype="REGION", keywords=cfg.location_keywords)
    industries = resolve_ids(cfg, ptype="SALES_INDUSTRY", keywords=cfg.industry_keywords)
    body = search_body(
        cfg,
        location_ids=[x["id"] for x in locations],
        industry_ids=[x["id"] for x in industries],
    )
    _print(
        {
            "account_id_suffix": cfg.unipile_account_id[-4:],
            "require_premium": cfg.require_premium,
            "min_employees": cfg.min_employees,
            "role_titles": list(cfg.role_titles),
            "seniority": list(cfg.seniority_include),
            "locations": locations,
            "industries": industries,
            "search_body": body,
        }
    )
    return 0


def cmd_discover(cfg: CdeConfig, *, max_keep: int, max_raw: int, no_industry: bool) -> int:
    result = discover(
        cfg,
        max_keep=max_keep,
        max_raw=max_raw,
        include_industry=not no_industry,
    )
    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "discover_last.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    slim = {
        **{k: v for k, v in result.items() if k != "kept"},
        "kept": [
            {
                "name": r.get("name"),
                "job_title": r.get("job_title"),
                "company_name": r.get("company_name"),
                "company_employees": r.get("company_employees"),
                "industry": r.get("industry"),
                "location": r.get("location"),
                "premium": r.get("premium"),
                "open_profile": r.get("open_profile"),
                "linkedin_url": r.get("linkedin_url"),
                "hard_reject": r.get("hard_reject"),
            }
            for r in result.get("kept") or []
        ],
    }
    _print(slim)
    print(f"\nWrote {path}", file=sys.stderr)
    return 0 if not result.get("errors") else 1


def cmd_ensure_schema(cfg: CdeConfig) -> int:
    from .nocodb_schema import ensure_schema

    out = ensure_schema(cfg=cfg)
    _print(out)
    return 0 if out.get("ok") else 1


def cmd_sync(cfg: CdeConfig, *, path: str | None) -> int:
    from .nocodb import sync_leads

    src = Path(path) if path else ROOT / "data" / "discover_last.json"
    if not src.exists():
        print(f"missing discover file: {src}", file=sys.stderr)
        return 1
    payload = json.loads(src.read_text(encoding="utf-8"))
    leads = payload.get("kept") if isinstance(payload, dict) else payload
    if not isinstance(leads, list):
        print("discover file has no kept list", file=sys.stderr)
        return 1
    out = sync_leads(leads, cfg=cfg)
    _print({k: v for k, v in out.items() if k != "actions"} | {"actions": out.get("actions")})
    return 0 if out.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cde_salesnav")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("queries", help="Resolve Unipile SN parameter IDs (small API spend)")
    d = sub.add_parser("discover", help="Search SN via Unipile and keep premium ICP matches")
    d.add_argument("--max-keep", type=int, default=20)
    d.add_argument("--max-raw", type=int, default=80)
    d.add_argument("--no-industry", action="store_true", help="Skip industry filter (broader test)")
    sub.add_parser("ensure-schema", help="Create missing NocoDB columns from prospecting_es_formacion")
    s = sub.add_parser("sync", help="Clean discover hits and upsert into NocoDB cde_salesnav")
    s.add_argument("--file", default="", help="Path to discover_last.json")
    args = parser.parse_args(argv)
    cfg = CdeConfig.from_env()
    if args.cmd == "queries":
        return cmd_queries(cfg)
    if args.cmd == "discover":
        return cmd_discover(cfg, max_keep=args.max_keep, max_raw=args.max_raw, no_industry=args.no_industry)
    if args.cmd == "ensure-schema":
        return cmd_ensure_schema(cfg)
    if args.cmd == "sync":
        return cmd_sync(cfg, path=args.file or None)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
