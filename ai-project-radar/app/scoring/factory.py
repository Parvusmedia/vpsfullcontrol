from __future__ import annotations

from app.config import Settings
from app.scoring.base import Scorer
from app.scoring.mock import MockScorer
from app.scoring.openai_scorer import OpenAIScorer


def get_scorer(settings: Settings) -> Scorer:
    if settings.use_mocks:
        return MockScorer()
    return OpenAIScorer(settings.openai_api_key, settings.openai_model)
