from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from app.db import Database
from app.models import Opportunity
from app.proposal.base import ProposalGenerator
from app.telegram.client import TelegramClient
from app.telegram.formatter import (
    alert_keyboard,
    format_alert,
    format_proposal,
    format_scan_summary,
    format_stats,
    proposal_keyboard,
)

logger = logging.getLogger(__name__)

ScanFn = Callable[[], Awaitable[Any]]


class TelegramBot:
    def __init__(
        self,
        client: TelegramClient,
        db: Database,
        proposal: ProposalGenerator,
        allowed_chat_id: str,
        scan_fn: ScanFn | None = None,
        min_score: float = 8.0,
    ) -> None:
        self.client = client
        self.db = db
        self.proposal = proposal
        self.allowed_chat_id = str(allowed_chat_id)
        self.scan_fn = scan_fn
        self.min_score = min_score

    def _authorized(self, chat_id: str | int | None) -> bool:
        if not self.allowed_chat_id:
            return False
        return str(chat_id) == self.allowed_chat_id

    async def notify_opportunity(self, opp: Opportunity) -> int | None:
        payload = await self.client.send_message(
            format_alert(opp),
            reply_markup=alert_keyboard(opp),
        )
        result = payload.get("result") or {}
        return result.get("message_id")

    async def handle_update(self, update: dict[str, Any]) -> None:
        if "callback_query" in update:
            await self._handle_callback(update["callback_query"])
            return
        message = update.get("message") or update.get("edited_message")
        if not message:
            return
        chat_id = str((message.get("chat") or {}).get("id", ""))
        if not self._authorized(chat_id):
            logger.info("Ignoring Telegram chat_id=%s", chat_id)
            return
        text = (message.get("text") or "").strip()
        if not text.startswith("/"):
            return
        command = text.split()[0].split("@")[0].lower()
        await self.handle_command(command, chat_id)

    async def handle_command(self, command: str, chat_id: str) -> None:
        if command == "/scan":
            await self.client.send_message("🛰 Running radar scan…", chat_id=chat_id)
            if self.scan_fn is None:
                await self.client.send_message("Scan is not wired in this process.", chat_id=chat_id)
                return
            summary = await self.scan_fn()
            await self.client.send_message(format_scan_summary(summary), chat_id=chat_id)
            return
        if command == "/latest":
            items = self.db.latest_qualified(self.min_score, limit=5)
            if not items:
                await self.client.send_message("No qualified opportunities yet.", chat_id=chat_id)
                return
            for opp in items:
                if opp.scoring is None:
                    continue
                await self.client.send_message(
                    format_alert(opp),
                    chat_id=chat_id,
                    reply_markup=alert_keyboard(opp),
                )
            return
        if command == "/stats":
            await self.client.send_message(format_stats(self.db.stats()), chat_id=chat_id)
            return
        if command == "/start":
            await self.client.send_message(
                "AI Project Radar ready.\n\n/scan — run now\n/latest — score ≥ 8\n/stats — today",
                chat_id=chat_id,
            )

    async def _handle_callback(self, callback: dict[str, Any]) -> None:
        data = callback.get("data") or ""
        chat = (callback.get("message") or {}).get("chat") or {}
        chat_id = str(chat.get("id", ""))
        callback_id = callback.get("id") or ""
        if not self._authorized(chat_id):
            await self.client.answer_callback(callback_id, "Unauthorized")
            return
        if ":" not in data:
            await self.client.answer_callback(callback_id)
            return
        action, raw_id = data.split(":", 1)
        try:
            opp_id = int(raw_id)
        except ValueError:
            await self.client.answer_callback(callback_id, "Bad id")
            return
        opp = self.db.get(opp_id)
        if opp is None:
            await self.client.answer_callback(callback_id, "Not found")
            return
        if action == "p":
            await self.client.answer_callback(callback_id, "Preparing proposal…")
            letter = await self.proposal.generate(opp, rewrite=False)
            self.db.save_proposal(opp_id, letter)
            opp.proposal = letter
            await self.client.send_message(
                format_proposal(opp, letter),
                chat_id=chat_id,
                reply_markup=proposal_keyboard(opp),
            )
            return
        if action == "r":
            await self.client.answer_callback(callback_id, "Rewriting…")
            letter = await self.proposal.generate(opp, rewrite=True)
            self.db.save_proposal(opp_id, letter)
            opp.proposal = letter
            await self.client.send_message(
                format_proposal(opp, letter),
                chat_id=chat_id,
                reply_markup=proposal_keyboard(opp),
            )
            return
        if action == "a":
            self.db.set_status(opp_id, "applied")
            await self.client.answer_callback(callback_id, "Marked applied")
            await self.client.send_message(f"✅ Marked applied: {opp.title}", chat_id=chat_id)
            return
        if action == "d":
            self.db.set_status(opp_id, "discarded")
            await self.client.answer_callback(callback_id, "Discarded")
            await self.client.send_message(f"❌ Discarded: {opp.title}", chat_id=chat_id)
            return
        await self.client.answer_callback(callback_id)
