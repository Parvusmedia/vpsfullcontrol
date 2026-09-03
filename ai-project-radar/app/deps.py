from __future__ import annotations

from app.config import Settings
from app.db import Database
from app.pipeline import Pipeline
from app.proposal.factory import get_proposal_generator
from app.scoring.factory import get_scorer
from app.search.factory import get_search_provider
from app.telegram.bot import TelegramBot
from app.telegram.client import RecordingTelegramClient, TelegramClient


class AppContext:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = Database(settings.database_path)
        self.search = get_search_provider(settings)
        self.scorer = get_scorer(settings)
        self.proposal = get_proposal_generator(settings)
        if settings.use_mocks:
            self.telegram_client: TelegramClient = RecordingTelegramClient(
                token=settings.telegram_bot_token or "mock",
                chat_id=settings.telegram_chat_id or "0",
            )
        else:
            self.telegram_client = TelegramClient(
                settings.telegram_bot_token,
                settings.telegram_chat_id,
            )
        self.bot = TelegramBot(
            client=self.telegram_client,
            db=self.db,
            proposal=self.proposal,
            allowed_chat_id=settings.telegram_chat_id or "0",
            min_score=settings.min_notify_score,
        )
        self.pipeline = Pipeline(
            settings=settings,
            db=self.db,
            search=self.search,
            scorer=self.scorer,
            bot=self.bot,
            proposal=self.proposal,
        )
        self.bot.scan_fn = self.pipeline.run

    def close(self) -> None:
        self.db.close()
