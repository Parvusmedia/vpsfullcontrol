"""CLI: queries | discover."""

from __future__ import annotations

import argparse
import json
import sys

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cde_salesnav")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("queries", help="Resolve Unipile SN parameter IDs (small API spend)")
    d = sub.add_parser("discover", help="Search SN via Unipile and keep premium ICP matches")
    d.add_argument("--max-keep", type=int, default=20)
    d.add_argument("--max-raw", type=int, default=80)
    d.add_argument("--no-industry", action="store_true", help="Skip industry filter (broader test)")
    args = parser.parse_args(argv)
    cfg = CdeConfig.from_env()
    if args.cmd == "queries":
        return cmd_queries(cfg)
    if args.cmd == "discover":
        return cmd_discover(cfg, max_keep=args.max_keep, max_raw=args.max_raw, no_industry=args.no_industry)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
