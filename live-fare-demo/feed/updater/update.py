#!/usr/bin/env python3
"""Generate static fare JSON for Nginx. No per-impression backend."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "feed" / "source" / "fares.json"
PUBLIC_DIR = ROOT / "feed" / "public"
PUBLIC_FEED = PUBLIC_DIR / "MAD.json"
HEALTH_PATH = PUBLIC_DIR / "health.json"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {path}")
    return data


def atomic_write_json(path: Path, payload: Any) -> None:
    """Write via MAD.tmp.json (or health.tmp.json) then rename."""
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f"{path.stem}.tmp.json"
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    tmp.write_text(encoded, encoding="utf-8")
    os.replace(tmp, path)


def fare_key(fare: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(fare.get("destination", "")),
        str(fare.get("month", "")),
        str(fare.get("currency", "EUR")),
    )


def last_prices(public: dict[str, Any] | None) -> dict[tuple[str, str, str], int]:
    out: dict[tuple[str, str, str], int] = {}
    if not public:
        return out
    for fare in public.get("fares") or []:
        try:
            out[fare_key(fare)] = int(fare["price"])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def jitter_price(current: int, min_price: int, max_price: int) -> int:
    delta = random.randint(-6, 6)
    if delta == 0:
        delta = random.choice((-1, 1))
    nxt = current + delta
    return max(min_price, min(max_price, nxt))


def build_deeplink(base: str, origin: str, destination: str, month: str) -> str:
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}origin={origin}&destination={destination}&month={month}"


def public_fare(item: dict[str, Any], origin: str, deeplink_base: str, price: int) -> dict[str, Any]:
    destination = str(item["destination"])
    month = str(item["month"])
    return {
        "destination": destination,
        "destination_name": str(item.get("destination_name") or destination),
        "month": month,
        "price": int(price),
        "currency": str(item.get("currency") or "EUR"),
        "deeplink": build_deeplink(deeplink_base, origin, destination, month),
    }


def generate_feed(
    source: dict[str, Any],
    previous: dict[str, Any] | None,
    *,
    jitter: bool,
) -> dict[str, Any]:
    origin = str(source.get("origin") or "MAD")
    deeplink_base = os.environ.get("DEEPLINK_BASE") or str(
        source.get("deeplink_base") or "https://example.com/book"
    )
    prev = last_prices(previous)
    fares = []
    for item in source.get("fares") or []:
        key = fare_key(item)
        base_price = int(item["price"])
        min_price = int(item.get("min_price", max(1, base_price - 40)))
        max_price = int(item.get("max_price", base_price + 50))
        current = prev.get(key, base_price)
        price = jitter_price(current, min_price, max_price) if jitter else current
        fares.append(public_fare(item, origin, deeplink_base, price))
    return {
        "origin": origin,
        "updated_at": iso_z(utc_now()),
        "fares": fares,
    }


def write_health(feed_path: Path, feed: dict[str, Any] | None) -> dict[str, Any]:
    exists = feed_path.is_file()
    age = None
    updated_at = None
    fares_count = 0
    status = "ok"
    if feed:
        updated_at = str(feed.get("updated_at") or "")
        fares_count = len(feed.get("fares") or [])
        parsed = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        age = max(0, int((utc_now() - parsed).total_seconds()))
    elif exists:
        age = max(0, int(time.time() - feed_path.stat().st_mtime))
        status = "degraded"
    else:
        status = "missing"
    payload = {
        "status": status,
        "feed_exists": exists,
        "feed_age_seconds": age,
        "updated_at": updated_at,
        "fares_count": fares_count,
    }
    atomic_write_json(HEALTH_PATH, payload)
    return payload


def set_fare(source: dict[str, Any], origin: str, dest: str, month: str, price: int) -> dict[str, Any]:
    if str(source.get("origin")) != origin:
        raise SystemExit(f"Source origin is {source.get('origin')}, not {origin}")
    matched = False
    for item in source.get("fares") or []:
        if item.get("destination") == dest and item.get("month") == month:
            item["price"] = price
            item["min_price"] = max(1, price - 20)
            item["max_price"] = price + 20
            matched = True
            break
    if not matched:
        raise SystemExit(f"No fare {origin}-{dest}-{month} in source")
    atomic_write_json(SOURCE_PATH, source)
    return source


def apply_stale(feed: dict[str, Any], minutes: int) -> dict[str, Any]:
    feed["updated_at"] = iso_z(utc_now() - timedelta(minutes=minutes))
    return feed


def run_update(*, jitter: bool, stale_minutes: int | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    source = load_json(SOURCE_PATH)
    previous = load_json(PUBLIC_FEED) if PUBLIC_FEED.is_file() else None
    feed = generate_feed(source, previous, jitter=jitter)
    if stale_minutes is not None:
        feed = apply_stale(feed, stale_minutes)
    atomic_write_json(PUBLIC_FEED, feed)
    write_health(PUBLIC_FEED, feed)
    elapsed_ms = (time.perf_counter() - started) * 1000
    stamp = utc_now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"{stamp}\nUpdated {PUBLIC_FEED.name}\n{len(feed['fares'])} fares\n"
        f"generation_time={elapsed_ms:.0f}ms",
        flush=True,
    )
    return feed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live fare static JSON updater")
    parser.add_argument("--once", action="store_true", help="Run a single jitter update (default)")
    parser.add_argument("--no-jitter", action="store_true", help="Rewrite JSON without changing prices")
    parser.add_argument("--loop", action="store_true", help="Loop forever (local docker)")
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.environ.get("UPDATE_INTERVAL_SECONDS", "60")),
        help="Loop interval in seconds",
    )
    parser.add_argument(
        "--set",
        nargs=4,
        metavar=("ORIGIN", "DEST", "MONTH", "PRICE"),
        help="Pin a fare in source and publish immediately",
    )
    parser.add_argument(
        "--stale",
        type=int,
        metavar="MINUTES",
        help="Publish current fares with updated_at shifted to the past",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    if args.set:
        origin, dest, month, price_s = args.set
        source = load_json(SOURCE_PATH)
        set_fare(source, origin.upper(), dest.upper(), month, int(price_s))
        previous = load_json(PUBLIC_FEED) if PUBLIC_FEED.is_file() else None
        feed = generate_feed(source, previous, jitter=False)
        # Force the pinned price even if previous JSON still has the old value.
        for fare in feed["fares"]:
            if fare["destination"] == dest.upper() and fare["month"] == month:
                fare["price"] = int(price_s)
        feed["updated_at"] = iso_z(utc_now())
        atomic_write_json(PUBLIC_FEED, feed)
        write_health(PUBLIC_FEED, feed)
        print(f"Pinned {origin.upper()}-{dest.upper()}-{month} to {price_s}", flush=True)
        return 0

    if args.stale is not None:
        run_update(jitter=False, stale_minutes=args.stale)
        return 0

    if args.loop:
        while True:
            run_update(jitter=not args.no_jitter)
            time.sleep(max(1, args.interval))

    run_update(jitter=not args.no_jitter)
    return 0


if __name__ == "__main__":
    sys.exit(main())
