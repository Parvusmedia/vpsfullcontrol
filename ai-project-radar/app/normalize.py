from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "gclsrc",
    "mc_cid",
    "mc_eid",
    "igshid",
    "si",
    "ref",
    "ref_src",
    "trk",
    "trackingId",
}

PLATFORM_HOSTS = (
    ("upwork.com", "Upwork"),
    ("freelancer.com", "Freelancer"),
    ("linkedin.com", "LinkedIn"),
    ("contra.com", "Contra"),
    ("toptal.com", "Toptal"),
    ("guru.com", "Guru"),
)


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for needle, name in PLATFORM_HOSTS:
        if host == needle or host.endswith("." + needle):
            return name
    return host.split(":")[0] or "web"


def normalize_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+", "/", parsed.path or "")
    if path.endswith("/") and path != "/":
        path = path[:-1]
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(sorted(query_pairs))
    return urlunparse((scheme, netloc, path, "", query, ""))


def content_hash(url: str, title: str, snippet: str) -> str:
    payload = f"{normalize_url(url)}\n{title.strip().lower()}\n{snippet.strip().lower()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def relative_time(published_at: str | None, first_seen_iso: str | None = None) -> str:
    from datetime import datetime, timezone

    raw = published_at or first_seen_iso or ""
    if not raw:
        return "recently"
    lowered = raw.strip().lower()
    if "ago" in lowered or lowered in {"just now", "today", "yesterday"}:
        return raw.strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw.strip()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())
    if seconds < 90:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    days = seconds // 86400
    return f"{days}d ago"
