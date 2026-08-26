import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger("movistar-parati.telegram")


class TelegramClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}"

    @property
    def configured(self) -> bool:
        return bool(self.settings.telegram_bot_token)

    async def api(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            logger.warning("Telegram token not configured; skipping %s", method)
            return {"ok": False, "description": "token_missing"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{self.base}/{method}", json=payload)
            data = resp.json()
            if not data.get("ok"):
                logger.error("Telegram API %s failed: %s", method, data)
            return data

    async def api_multipart(self, method: str, data: dict[str, str], files: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            logger.warning("Telegram token not configured; skipping %s", method)
            return {"ok": False, "description": "token_missing"}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.base}/{method}", data=data, files=files)
            payload = resp.json()
            if not payload.get("ok"):
                logger.error("Telegram API %s failed: %s", method, payload)
            return payload

    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        return await self.api("sendMessage", payload)

    async def send_photo_bytes(
        self,
        chat_id: int,
        photo_bytes: bytes,
        *,
        caption: str,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        data: dict[str, str] = {
            "chat_id": str(chat_id),
            "caption": caption,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        files = {"photo": ("product.jpg", photo_bytes, "image/jpeg")}
        return await self.api_multipart("sendPhoto", data, files)

    async def edit_message_media_bytes(
        self,
        chat_id: int,
        message_id: int,
        photo_bytes: bytes,
        *,
        caption: str,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        media = json.dumps(
            {
                "type": "photo",
                "media": "attach://photo",
                "caption": caption,
                "parse_mode": parse_mode,
            }
        )
        data: dict[str, str] = {
            "chat_id": str(chat_id),
            "message_id": str(message_id),
            "media": media,
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        files = {"photo": ("product.jpg", photo_bytes, "image/jpeg")}
        return await self.api_multipart("editMessageMedia", data, files)

    async def answer_callback(self, callback_query_id: str, text: str = "") -> dict[str, Any]:
        return await self.api("answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text})

    async def set_webhook(self, url: str, secret_token: str) -> dict[str, Any]:
        return await self.api(
            "setWebhook",
            {"url": url, "secret_token": secret_token, "drop_pending_updates": True},
        )

    async def get_webhook_info(self) -> dict[str, Any]:
        return await self.api("getWebhookInfo", {})

    async def set_my_commands(self, commands: list[dict[str, str]]) -> dict[str, Any]:
        return await self.api(
            "setMyCommands",
            {
                "commands": commands,
                "scope": {"type": "default"},
                "language_code": "es",
            },
        )

    async def set_my_name(self, name: str) -> dict[str, Any]:
        return await self.api("setMyName", {"name": name})

    async def set_my_description(self, description: str) -> dict[str, Any]:
        return await self.api("setMyDescription", {"description": description})

    async def set_my_short_description(self, short_description: str) -> dict[str, Any]:
        return await self.api("setMyShortDescription", {"short_description": short_description})

    async def set_chat_menu_button(self, menu_type: str = "commands") -> dict[str, Any]:
        return await self.api(
            "setChatMenuButton",
            {"menu_button": {"type": menu_type}},
        )


telegram_client = TelegramClient()
