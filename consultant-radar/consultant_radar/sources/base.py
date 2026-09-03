from __future__ import annotations

from typing import Any, Protocol

from ..models import Job


class Source(Protocol):
    name: str

    def fetch(self, company: dict[str, Any]) -> list[Job]:
        ...
