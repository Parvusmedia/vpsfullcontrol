from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Job:
    company_id: str
    company_name: str
    source: str
    source_id: str
    title: str
    location: str
    url: str
    posted_at: str = ""
    brands: tuple[str, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def uid(self) -> str:
        return f"{self.company_id}:{self.source}:{self.source_id}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["uid"] = self.uid
        payload["brands"] = list(self.brands)
        return payload
