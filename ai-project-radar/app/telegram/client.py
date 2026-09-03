from __future__ import annotations

from typing import Any

import httpx


class TelegramClient:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = str(chat_id)
        self.base = f"https://api.telegram.org/bot{token}"

    async def send_message(
        self,
        text: str,
        *,
        chat_id: str | None = None,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id or self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self._post("sendMessage", payload)

    async def answer_callback(self, callback_id: str, text: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"callback_query_id": callback_id}
        if text:
            payload["text"] = text
        return await self._post("answerCallbackQuery", payload)

    async def get_updates(self, offset: int | None = None, timeout: int = 25) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
        if offset is not None:
            payload["offset"] = offset
        data = await self._post("getUpdates", payload)
        return data.get("result") or []

    async def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(f"{self.base}/{method}", json=payload)
            response.raise_for_status()
            data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram error: {data}")
        return data


class RecordingTelegramClient(TelegramClient):
    """In-memory Telegram client for tests and USE_MOCKS."""

    def __init__(self, token: str = "mock-token", chat_id: str = "12345") -> None:
        super().__init__(token, chat_id)
        self.messages: list[dict[str, Any]] = []
        self.callbacks_answered: list[str] = []

    async def send_message(
        self,
        text: str,
        *,
        chat_id: str | None = None,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        message_id = len(self.messages) + 1
        record = {
            "message_id": message_id,
            "chat_id": chat_id or self.chat_id,
            "text": text,
            "reply_markup": reply_markup,
            "parse_mode": parse_mode,
        }
        self.messages.append(record)
        return {"ok": True, "result": {"message_id": message_id}}

    async def answer_callback(self, callback_id: str, text: str = "") -> dict[str, Any]:
        self.callbacks_answered.append(callback_id)
        return {"ok": True}

    async def get_updates(self, offset: int | None = None, timeout: int = 25) -> list[dict[str, Any]]:
        return []
