from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import OpportunityScore, SearchResult


class Scorer(ABC):
    @abstractmethod
    async def score(self, result: SearchResult) -> OpportunityScore:
        """Score a search result against the consultant profile."""
