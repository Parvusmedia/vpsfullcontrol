#!/usr/bin/env python3
"""Generate static fare JSON for Nginx. No per-impression backend."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "feed" / "source" / "routes.json"
PUBLIC_DIR = ROOT / "feed" / "public"
NETWORK_FEED = PUBLIC_DIR / "network.json"
HEALTH_PATH = PUBLIC_DIR / "health.json"
SEASONAL = {"2026-10": 1.0, "2026-11": 1.05, "2026-12": 1.10}


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
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f"{path.stem}.tmp.json"
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    tmp.write_text(encoded, encoding="utf-8")
    os.replace(tmp, path)


def fare_key(fare: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(fare.get("origin", "")),
        str(fare.get("destination", "")),
        str(fare.get("month", "")),
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
    span = max(3, min(40, round(current * 0.012)))
    delta = random.randint(-span, span)
    if delta == 0:
        delta = random.choice((-1, 1))
    nxt = current + delta
    return max(min_price, min(max_price, nxt))


def build_deeplink(base: str, origin: str, destination: str, month: str) -> str:
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}origin={origin}&destination={destination}&month={month}"


def origin_meta(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["code"]): item for item in source.get("origins") or []}


def months_of(source: dict[str, Any]) -> list[str]:
    months = list(source.get("months") or ["2026-10", "2026-11", "2026-12"])
    return months


def month_base_price(route: dict[str, Any], month: str) -> int:
    pinned = (route.get("prices") or {}).get(month)
    if pinned is not None:
        return int(pinned)
    base = int(route["price"])
    factor = SEASONAL.get(month, 1.0)
    return max(1, round(base * factor))


def public_fare(route: dict[str, Any], origin: dict[str, Any], month: str, price: int, deeplink_base: str) -> dict[str, Any]:
    destination = str(route["destination"])
    origin_code = str(route["origin"])
    return {
        "origin": origin_code,
        "origin_name": str(origin.get("name") or origin_code),
        "destination": destination,
        "destination_name": str(route.get("destination_name") or destination),
        "month": month,
        "price": int(price),
        "currency": str(route.get("currency") or origin.get("currency") or "SAR"),
        "deeplink": build_deeplink(deeplink_base, origin_code, destination, month),
    }


def generate_network(
    source: dict[str, Any],
    previous: dict[str, Any] | None,
    *,
    jitter: bool,
) -> dict[str, Any]:
    deeplink_base = os.environ.get("DEEPLINK_BASE") or str(
        source.get("deeplink_base") or "https://www.saudia.com/book"
    )
    origins = origin_meta(source)
    prev = last_prices(previous)
    fares: list[dict[str, Any]] = []
    for route in source.get("routes") or []:
        origin_code = str(route["origin"])
        origin = origins.get(origin_code) or {"code": origin_code, "name": origin_code}
        for month in months_of(source):
            base_price = month_base_price(route, month)
            min_price = int(route.get("min_price", max(1, round(base_price * 0.86))))
            max_price = int(route.get("max_price", round(base_price * 1.14)))
            key = (origin_code, str(route["destination"]), month)
            current = prev.get(key, base_price)
            price = jitter_price(current, min_price, max_price) if jitter else current
            fares.append(public_fare(route, origin, month, price, deeplink_base))
    return {
        "updated_at": iso_z(utc_now()),
        "origins": source.get("origins") or [],
        "fares": fares,
    }


def split_origin_feeds(network: dict[str, Any]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    names = {str(item["code"]): str(item.get("name") or item["code"]) for item in network.get("origins") or []}
    for fare in network.get("fares") or []:
        origin = str(fare["origin"])
        slim = {k: v for k, v in fare.items() if k not in ("origin", "origin_name")}
        grouped[origin].append(slim)
    out = {}
    for origin, fares in grouped.items():
        out[origin] = {
            "origin": origin,
            "origin_name": names.get(origin, origin),
            "updated_at": network["updated_at"],
            "fares": fares,
        }
    return out


def write_health(network: dict[str, Any] | None) -> dict[str, Any]:
    exists = NETWORK_FEED.is_file()
    age = None
    updated_at = None
    fares_count = 0
    origins: list[str] = []
    status = "ok"
    if network:
        updated_at = str(network.get("updated_at") or "")
        fares_count = len(network.get("fares") or [])
        origins = [str(item["code"]) for item in network.get("origins") or []]
        parsed = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        age = max(0, int((utc_now() - parsed).total_seconds()))
    elif exists:
        age = max(0, int(time.time() - NETWORK_FEED.stat().st_mtime))
        status = "degraded"
    else:
        status = "missing"
    payload = {
        "status": status,
        "feed_exists": exists,
        "feed_age_seconds": age,
        "updated_at": updated_at,
        "fares_count": fares_count,
        "origins": origins,
    }
    atomic_write_json(HEALTH_PATH, payload)
    return payload


def set_fare(source: dict[str, Any], origin: str, dest: str, month: str, price: int) -> dict[str, Any]:
    matched = False
    for route in source.get("routes") or []:
        if route.get("origin") == origin and route.get("destination") == dest:
            prices = dict(route.get("prices") or {})
            prices[month] = price
            route["prices"] = prices
            route["min_price"] = max(1, min(int(route.get("min_price", price)), price - 20, price))
            route["max_price"] = max(int(route.get("max_price", price)), price + 20, price)
            matched = True
            break
    if not matched:
        raise SystemExit(f"No route {origin}-{dest} in source")
    if month not in months_of(source):
        raise SystemExit(f"Month {month} is not in source months")
    atomic_write_json(SOURCE_PATH, source)
    return source


def apply_stale(feed: dict[str, Any], minutes: int) -> dict[str, Any]:
    stamp = iso_z(utc_now() - timedelta(minutes=minutes))
    feed["updated_at"] = stamp
    return feed


def publish(network: dict[str, Any]) -> None:
    atomic_write_json(NETWORK_FEED, network)
    origin_feeds = split_origin_feeds(network)
    wanted = {f"{code}.json" for code in origin_feeds}
    wanted.update({"network.json", "health.json"})
    for code, payload in origin_feeds.items():
        atomic_write_json(PUBLIC_DIR / f"{code}.json", payload)
    for stale in PUBLIC_DIR.glob("*.json"):
        if stale.name.endswith(".tmp.json"):
            continue
        if stale.name not in wanted:
            stale.unlink()
    write_health(network)


def run_update(*, jitter: bool, stale_minutes: int | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    source = load_json(SOURCE_PATH)
    previous = load_json(NETWORK_FEED) if NETWORK_FEED.is_file() else None
    network = generate_network(source, previous, jitter=jitter)
    if stale_minutes is not None:
        network = apply_stale(network, stale_minutes)
        for fare in network["fares"]:
            pass
        origin_feeds = split_origin_feeds(network)
        for payload in origin_feeds.values():
            payload["updated_at"] = network["updated_at"]
    publish(network)
    elapsed_ms = (time.perf_counter() - started) * 1000
    stamp = utc_now().strftime("%Y-%m-%d %H:%M:%S")
    origins = len(network.get("origins") or [])
    print(
        f"{stamp}\nUpdated network.json + {origins} origin files\n"
        f"{len(network['fares'])} fares\ngeneration_time={elapsed_ms:.0f}ms",
        flush=True,
    )
    return network


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
        previous = load_json(NETWORK_FEED) if NETWORK_FEED.is_file() else None
        network = generate_network(source, previous, jitter=False)
        for fare in network["fares"]:
            if (
                fare["origin"] == origin.upper()
                and fare["destination"] == dest.upper()
                and fare["month"] == month
            ):
                fare["price"] = int(price_s)
        network["updated_at"] = iso_z(utc_now())
        publish(network)
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
