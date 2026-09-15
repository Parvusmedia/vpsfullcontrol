from __future__ import annotations

from typing import Any

from .greenhouse import GreenhouseSource
from .phenom import PhenomSource
from .rss import AvatureRssSource, RssSource
from .workday import WorkdaySource


def build_registry(**kwargs: Any) -> dict[str, Any]:
    return {
        "workday": WorkdaySource(**kwargs.get("workday", {})),
        "greenhouse": GreenhouseSource(**kwargs.get("greenhouse", {})),
        "rss": RssSource(**kwargs.get("rss", {})),
        "avature_rss": AvatureRssSource(**kwargs.get("avature_rss", kwargs.get("rss", {}))),
        "phenom": PhenomSource(**kwargs.get("phenom", {})),
    }
