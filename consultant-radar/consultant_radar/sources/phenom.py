from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urljoin
from urllib.request import OpenerDirector

from ..models import Job

JOB_HREF = re.compile(r"^/job/[^#?]+/\d+/?$")


class _JobLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.jobs: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        path = href.split("?", 1)[0]
        if JOB_HREF.match(path):
            self._current_href = path
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href is not None:
            title = " ".join(" ".join(self._chunks).split())
            self.jobs.append((self._current_href, title))
            self._current_href = None
            self._chunks = []


def parse_phenom_jobs(html: str, company: dict[str, Any], source_name: str = "phenom") -> list[Job]:
    parser = _JobLinkParser()
    parser.feed(html)
    seen: dict[str, Job] = {}
    base = company.get("base_url") or company.get("list_url") or ""
    for href, title in parser.jobs:
        source_id = href.rstrip("/").rsplit("/", 1)[-1]
        slug = href.strip("/").split("/")[1] if href.count("/") >= 2 else ""
        location = slug.split("-")[0].replace("%20", " ") if slug else ""
        if not title:
            title = slug.replace("-", " ")
        seen[source_id] = Job(
            company_id=company["id"],
            company_name=company["name"],
            source=source_name,
            source_id=source_id,
            title=title,
            location=location,
            url=urljoin(base.rstrip("/") + "/", href.lstrip("/")),
            brands=tuple(company.get("brands") or []),
            raw={"href": href},
        )
    return list(seen.values())


class PhenomSource:
    name = "phenom"

    def __init__(self, opener: OpenerDirector | None = None, get_text: Callable[..., str] | None = None):
        self.opener = opener
        self._get_text = get_text

    def _text(self, url: str) -> str:
        if self._get_text:
            return self._get_text(url)
        from ..http import get_text

        return get_text(url, opener=self.opener)

    def fetch(self, company: dict[str, Any]) -> list[Job]:
        jobs: dict[str, Job] = {}
        list_url = company["list_url"]
        max_pages = int(company.get("max_pages") or 4)
        page_size = int(company.get("page_size") or 50)
        for page in range(max_pages):
            start = page * page_size
            sep = "&" if "?" in list_url else "?"
            url = list_url if page == 0 else f"{list_url}{sep}from={start}&s=1"
            html = self._text(url)
            batch = parse_phenom_jobs(html, company, self.name)
            if not batch:
                break
            new_ids = 0
            for job in batch:
                if job.source_id not in jobs:
                    new_ids += 1
                jobs[job.source_id] = job
            if new_ids == 0:
                break
        return list(jobs.values())
