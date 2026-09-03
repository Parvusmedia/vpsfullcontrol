from __future__ import annotations

from typing import Any, Callable
from urllib.request import OpenerDirector

from ..models import Job

PAGE_SIZE = 20


class WorkdaySource:
    name = "workday"

    def __init__(self, opener: OpenerDirector | None = None, request_json: Callable[..., Any] | None = None):
        self.opener = opener
        self._request_json = request_json

    def _json(self, url: str, *, method: str = "GET", json_body: dict[str, Any] | None = None) -> Any:
        if self._request_json:
            return self._request_json(url, method=method, json_body=json_body)
        from ..http import get_json

        return get_json(url, method=method, json_body=json_body, opener=self.opener)

    def fetch(self, company: dict[str, Any]) -> list[Job]:
        host = company["host"]
        tenant = company["tenant"]
        site = company["site"]
        endpoint = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        search_texts = company.get("search_texts") or [""]
        facets = company.get("applied_facets") or {}
        max_pages = int(company.get("max_pages") or 5)
        jobs: dict[str, Job] = {}
        for search_text in search_texts:
            offset = 0
            for _page in range(max_pages):
                payload = {
                    "appliedFacets": facets,
                    "limit": PAGE_SIZE,
                    "offset": offset,
                    "searchText": search_text,
                }
                data = self._json(endpoint, method="POST", json_body=payload)
                postings = data.get("jobPostings") or []
                for posting in postings:
                    job = self._to_job(company, host, site, posting)
                    if not job.title or not job.source_id:
                        continue
                    jobs[job.uid] = job
                if len(postings) < PAGE_SIZE:
                    break
                offset += PAGE_SIZE
                total = int(data.get("total") or 0)
                if offset >= total:
                    break
        return list(jobs.values())

    def _to_job(self, company: dict[str, Any], host: str, site: str, posting: dict[str, Any]) -> Job:
        path = posting.get("externalPath") or ""
        source_id = (
            (posting.get("bulletFields") or [None])[0]
            or path.rsplit("_", 1)[-1]
            or path
        )
        location = ""
        bullets = posting.get("bulletFields") or []
        if len(bullets) > 1:
            location = bullets[1]
        locations_text = posting.get("locationsText") or posting.get("location") or ""
        if locations_text:
            location = locations_text
        title = (posting.get("title") or "").strip()
        url = f"https://{host}/{site}{path}" if path else ""
        brands = tuple(company.get("brands") or [])
        blob = f"{title} {location}".lower()
        if "song" in blob and "Accenture Song" not in brands:
            brands = brands + ("Accenture Song",)
        return Job(
            company_id=company["id"],
            company_name=company["name"],
            source=self.name,
            source_id=str(source_id),
            title=title,
            location=location or "",
            url=url,
            posted_at=posting.get("postedOn") or posting.get("postedOnDisplay") or "",
            brands=brands,
            raw=posting,
        )
