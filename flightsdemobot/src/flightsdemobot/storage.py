"""Persistent chat state and unlock storage."""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal

from flightsdemobot.i18n import Lang

Step = Literal[
    "idle",
    "await_key",
    "pick_origin",
    "pick_destination",
    "pick_departure",
    "pick_return",
    "pick_max_price",
]


@dataclass
class SearchDraft:
    origin: str | None = None
    destination: str | None = None
    departure: date | None = None
    return_date: date | None = None
    one_way: bool = False
    max_price_sar: int | None = None


@dataclass
class ChatState:
    lang: Lang = "en"
    unlocked: bool = False
    step: Step = "idle"
    draft: SearchDraft = field(default_factory=SearchDraft)


class Store:
    def __init__(self, path: Path, access_key: str) -> None:
        self._path = path
        self._access_key = access_key
        self._lock = threading.Lock()
        self._memory: dict[int, ChatState] = {}
        path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS unlocks (
                    chat_id INTEGER PRIMARY KEY,
                    unlocked INTEGER NOT NULL DEFAULT 0,
                    lang TEXT NOT NULL DEFAULT 'en',
                    draft_json TEXT NOT NULL DEFAULT '{}',
                    step TEXT NOT NULL DEFAULT 'idle'
                )
                """
            )
            conn.commit()
            conn.close()

    def get(self, chat_id: int) -> ChatState:
        with self._lock:
            if chat_id in self._memory:
                return self._memory[chat_id]
            conn = self._connect()
            row = conn.execute(
                "SELECT unlocked, lang, draft_json, step FROM unlocks WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
            conn.close()
            if row is None:
                state = ChatState()
                self._memory[chat_id] = state
                return state
            draft_data = json.loads(row["draft_json"] or "{}")
            draft = SearchDraft(
                origin=draft_data.get("origin"),
                destination=draft_data.get("destination"),
                departure=_parse_date(draft_data.get("departure")),
                return_date=_parse_date(draft_data.get("return_date")),
                one_way=bool(draft_data.get("one_way")),
                max_price_sar=draft_data.get("max_price_sar"),
            )
            state = ChatState(
                lang=row["lang"] if row["lang"] in ("en", "ar") else "en",
                unlocked=bool(row["unlocked"]),
                step=row["step"] if row["step"] else "idle",
                draft=draft,
            )
            self._memory[chat_id] = state
            return state

    def save(self, chat_id: int, state: ChatState) -> None:
        with self._lock:
            self._memory[chat_id] = state
            draft_json = json.dumps(_draft_to_dict(state.draft))
            conn = self._connect()
            conn.execute(
                """
                INSERT INTO unlocks (chat_id, unlocked, lang, draft_json, step)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    unlocked = excluded.unlocked,
                    lang = excluded.lang,
                    draft_json = excluded.draft_json,
                    step = excluded.step
                """,
                (
                    chat_id,
                    1 if state.unlocked else 0,
                    state.lang,
                    draft_json,
                    state.step,
                ),
            )
            conn.commit()
            conn.close()

    def verify_key(self, chat_id: int, key: str) -> bool:
        if key.strip() != self._access_key:
            return False
        state = self.get(chat_id)
        state.unlocked = True
        state.step = "idle"
        self.save(chat_id, state)
        return True

    def lock(self, chat_id: int) -> None:
        state = self.get(chat_id)
        state.unlocked = False
        state.step = "await_key"
        self.save(chat_id, state)


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    y, m, d = map(int, str(value).split("-"))
    return date(y, m, d)


def _draft_to_dict(draft: SearchDraft) -> dict[str, Any]:
    return {
        "origin": draft.origin,
        "destination": draft.destination,
        "departure": draft.departure.isoformat() if draft.departure else None,
        "return_date": draft.return_date.isoformat() if draft.return_date else None,
        "one_way": draft.one_way,
        "max_price_sar": draft.max_price_sar,
    }
