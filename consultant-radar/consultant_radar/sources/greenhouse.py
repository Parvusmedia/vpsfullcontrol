from __future__ import annotations

from typing import Any, Callable
from urllib.request import OpenerDirector

from ..models import Job


class GreenhouseSource:
    name = "greenhouse"

    def __init__(self, opener: OpenerDirector | None = None, request_json: Callable[..., Any] | None = None):
        self.opener = opener
        self._request_json = request_json

    def _json(self, url: str) -> Any:
        if self._request_json:
            return self._request_json(url)
        from ..http import get_json

        return get_json(url, opener=self.opener)

    def fetch(self, company: dict[str, Any]) -> list[Job]:
        board = company["board"]
        data = self._json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
        jobs = []
        for posting in data.get("jobs") or []:
            location = ""
            loc = posting.get("location") or {}
            if isinstance(loc, dict):
                location = loc.get("name") or ""
            jobs.append(
                Job(
                    company_id=company["id"],
                    company_name=company["name"],
                    source=self.name,
                    source_id=str(posting.get("id") or posting.get("internal_job_id") or ""),
                    title=posting.get("title") or "",
                    location=location,
                    url=posting.get("absolute_url") or "",
                    posted_at=posting.get("updated_at") or posting.get("created_at") or "",
                    brands=tuple(company.get("brands") or []),
                    raw=posting,
                )
            )
        return jobs
