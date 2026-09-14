"""Infer corporate email patterns from known addresses and guess for peers."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable


def _strip_accents(text: str) -> str:
    nk = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nk if not unicodedata.combining(c))


def norm_token(text: str) -> str:
    s = _strip_accents(text or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def name_tokens(text: str) -> list[str]:
    raw = _strip_accents(text or "").lower().replace("-", " ")
    parts = re.split(r"[\s,]+", raw)
    out: list[str] = []
    for p in parts:
        t = norm_token(p)
        if t and t not in {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos"}:
            # keep 'de' particles out of email tokens (common ES)
            out.append(t)
    return out


@dataclass(frozen=True)
class PatternGuess:
    email: str
    pattern: str
    domain: str
    evidence: int
    source_examples: tuple[str, ...]


def _local_parts(first: str, last: str) -> dict[str, str]:
    f_tokens = name_tokens(first)
    l_tokens = name_tokens(last)
    if not f_tokens:
        return {}
    first_n = f_tokens[0]
    last1 = l_tokens[0] if l_tokens else ""
    last2 = l_tokens[1] if len(l_tokens) > 1 else ""
    last_all = "".join(l_tokens)
    last_dot = ".".join(l_tokens) if l_tokens else ""
    out: dict[str, str] = {
        "first": first_n,
        "first.last1": f"{first_n}.{last1}" if last1 else first_n,
        "first_last1": f"{first_n}{last1}" if last1 else first_n,
        "flast1": f"{first_n[0]}{last1}" if last1 else first_n,
    }
    if last2:
        out["first.last1.last2"] = f"{first_n}.{last1}.{last2}"
        out["first.last_all_dot"] = f"{first_n}.{last_dot}"
    if last_all:
        out["first.last_compact"] = f"{first_n}.{last_all}"
    return out


def detect_pattern(first: str, last: str, email: str) -> str | None:
    email = (email or "").strip().lower()
    if "@" not in email:
        return None
    local = email.split("@", 1)[0]
    candidates = _local_parts(first, last)
    for name, value in candidates.items():
        if value == local:
            return name
    return None


def learn_domain_patterns(
    examples: Iterable[dict[str, Any]],
) -> dict[str, Counter]:
    """examples: {email, first_name, last_name, company_name?} → votes per domain/pattern."""
    votes: dict[str, Counter] = defaultdict(Counter)
    for row in examples:
        email = (row.get("email") or "").strip().lower()
        if "@" not in email:
            continue
        domain = email.split("@", 1)[1]
        pattern = detect_pattern(row.get("first_name") or "", row.get("last_name") or "", email)
        if pattern:
            votes[domain][pattern] += 1
            # Also remember example locals for evidence list
    return votes


def choose_pattern(votes: Counter, last_name: str) -> str | None:
    if not votes:
        return None
    l_tokens = name_tokens(last_name)
    ranked = votes.most_common()
    for pattern, _count in ranked:
        if pattern in {"first.last1.last2", "first.last_all_dot"} and len(l_tokens) < 2:
            continue
        if pattern != "first" and not l_tokens:
            continue
        return pattern
    return ranked[0][0]


def guess_email(
    *,
    first_name: str,
    last_name: str,
    domain: str,
    domain_votes: dict[str, Counter] | None = None,
    examples: Iterable[dict[str, Any]] | None = None,
) -> PatternGuess | None:
    domain = (domain or "").strip().lower()
    if not domain or "." not in domain:
        return None
    votes_map = domain_votes or {}
    if examples is not None and domain not in votes_map:
        votes_map = learn_domain_patterns(examples)
    votes = votes_map.get(domain) or Counter()
    if not votes:
        return None
    pattern = choose_pattern(votes, last_name)
    if not pattern:
        return None
    locals_map = _local_parts(first_name, last_name)
    local = locals_map.get(pattern)
    if not local:
        # fallback to first.last1
        local = locals_map.get("first.last1")
        pattern = "first.last1"
    if not local:
        return None
    evidence = int(votes.get(pattern) or votes.most_common(1)[0][1])
    ex_emails = tuple(
        sorted(
            {
                (e.get("email") or "").lower()
                for e in (examples or [])
                if (e.get("email") or "").lower().endswith("@" + domain)
            }
        )
    )
    return PatternGuess(
        email=f"{local}@{domain}",
        pattern=pattern,
        domain=domain,
        evidence=evidence,
        source_examples=ex_emails[:5],
    )


def examples_from_nocodb_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        email = (r.get("email") or "").strip()
        if not email or "@" not in email:
            continue
        out.append(
            {
                "email": email,
                "first_name": r.get("first_name") or "",
                "last_name": r.get("last_name") or "",
                "company_name": r.get("company_name") or "",
            }
        )
    return out
