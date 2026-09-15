from __future__ import annotations

import xml.etree.ElementTree as ET
from html import unescape
from typing import Any, Callable
from urllib.request import OpenerDirector

from ..models import Job


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return unescape(el.text).strip()


def parse_rss_jobs(xml_text: str, company: dict[str, Any], source_name: str) -> list[Job]:
    root = ET.fromstring(xml_text)
    jobs: list[Job] = []
    for item in root.findall("./channel/item"):
        title = _text(item.find("title"))
        if title.lower().startswith("no jobs currently available"):
            continue
        link = _text(item.find("link"))
        guid = _text(item.find("guid")) or link
        source_id = guid.rstrip("/").rsplit("/", 1)[-1] or guid
        location = ""
        if "(" in title and title.endswith(")"):
            location = title[title.rfind("(") + 1 : -1]
        jobs.append(
            Job(
                company_id=company["id"],
                company_name=company["name"],
                source=source_name,
                source_id=source_id,
                title=title,
                location=location,
                url=link or guid,
                posted_at=_text(item.find("pubDate")),
                brands=tuple(company.get("brands") or []),
                raw={"guid": guid, "title": title, "link": link},
            )
        )
    return jobs


class RssSource:
    name = "rss"

    def __init__(self, opener: OpenerDirector | None = None, get_text: Callable[..., str] | None = None):
        self.opener = opener
        self._get_text = get_text

    def _text(self, url: str) -> str:
        if self._get_text:
            return self._get_text(url)
        from ..http import get_text

        return get_text(url, opener=self.opener)

    def fetch(self, company: dict[str, Any]) -> list[Job]:
        xml_text = self._text(company["feed_url"])
        return parse_rss_jobs(xml_text, company, self.name)


class AvatureRssSource(RssSource):
    name = "avature_rss"
