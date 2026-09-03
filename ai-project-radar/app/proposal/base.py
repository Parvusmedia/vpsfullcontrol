from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import Opportunity


class ProposalGenerator(ABC):
    @abstractmethod
    async def generate(self, opportunity: Opportunity, *, rewrite: bool = False) -> str:
        """Return a 150–180 word cover letter."""
