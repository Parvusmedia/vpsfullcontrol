from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    published_at: datetime | None = None
    source: str = ""
    query: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


class OpportunityScore(BaseModel):
    score: float = Field(ge=0, le=10)
    title: str = ""
    company: str = ""
    country: str = ""
    published_at: str = ""
    budget: str = ""
    estimated_value: str = ""
    summary: str = ""
    why_fit: str = ""
    risks: str = ""
    recommendation: str = ""
    urgency: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"


class Opportunity(BaseModel):
    id: int | None = None
    url: str
    normalized_url: str
    content_hash: str
    platform: str = ""
    title: str = ""
    snippet: str = ""
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    score: float | None = None
    telegram_sent: bool = False
    telegram_message_id: int | None = None
    status: str = "new"
    scoring: OpportunityScore | None = None
    proposal: str | None = None
    query_used: str = ""


class ScanSummary(BaseModel):
    started_at: datetime
    finished_at: datetime | None = None
    results_found: int = 0
    new_saved: int = 0
    qualified: int = 0
    notified: int = 0
    error: str | None = None
