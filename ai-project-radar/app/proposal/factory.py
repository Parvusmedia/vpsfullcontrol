from __future__ import annotations

from app.config import Settings
from app.proposal.base import ProposalGenerator
from app.proposal.generator import OpenAIProposalGenerator
from app.proposal.mock import MockProposalGenerator


def get_proposal_generator(settings: Settings) -> ProposalGenerator:
    if settings.use_mocks:
        return MockProposalGenerator()
    return OpenAIProposalGenerator(settings.openai_api_key, settings.openai_model)
