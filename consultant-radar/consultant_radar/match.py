from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import Job

_WORD_RE = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WORD_RE.sub(" ", (text or "").strip().lower())


def _contains(blob: str, keyword: str) -> bool:
    needle = keyword.lower().strip()
    if not needle:
        return False
    if " " in needle or len(needle) > 6:
        return needle in blob
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", blob) is not None


@dataclass(frozen=True)
class Filters:
    include_keywords: tuple[str, ...]
    exclude_keywords: tuple[str, ...]
    exclude_title_prefixes: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Filters":
        return cls(
            include_keywords=tuple(payload.get("include_keywords") or []),
            exclude_keywords=tuple(payload.get("exclude_keywords") or []),
            exclude_title_prefixes=tuple(payload.get("exclude_title_prefixes") or []),
        )

    @classmethod
    def load(cls, path: Path) -> "Filters":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def haystack(job: Job) -> str:
    return _norm(f"{job.title} {job.location}")


def matched_keywords(job: Job, filters: Filters) -> list[str]:
    blob = haystack(job)
    hits = []
    for keyword in filters.include_keywords:
        if _contains(blob, keyword):
            hits.append(keyword)
    return hits


def is_excluded(job: Job, filters: Filters) -> bool:
    title = job.title or ""
    title_l = title.lower()
    for prefix in filters.exclude_title_prefixes:
        if title.startswith(prefix) or title_l.startswith(prefix.lower()):
            return True
    blob = haystack(job)
    for keyword in filters.exclude_keywords:
        if _contains(blob, keyword):
            return True
    return False


def classify(jobs: Iterable[Job], filters: Filters, *, require_include: bool = True) -> list[tuple[Job, list[str]]]:
    kept: list[tuple[Job, list[str]]] = []
    for job in jobs:
        if not (job.title or "").strip():
            continue
        if is_excluded(job, filters):
            continue
        hits = matched_keywords(job, filters)
        if require_include and not hits:
            continue
        kept.append((job, hits))
    return kept
