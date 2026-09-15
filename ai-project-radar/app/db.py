from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.models import Opportunity, OpportunityScore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_scoring(raw: str | None) -> OpportunityScore | None:
    if not raw:
        return None
    return OpportunityScore.model_validate_json(raw)


def _row_to_opportunity(row: sqlite3.Row) -> Opportunity:
    return Opportunity(
        id=row["id"],
        url=row["url"],
        normalized_url=row["normalized_url"],
        content_hash=row["content_hash"],
        platform=row["platform"] or "",
        title=row["title"] or "",
        snippet=row["snippet"] or "",
        first_seen=datetime.fromisoformat(row["first_seen"]) if row["first_seen"] else None,
        last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
        score=row["score"],
        telegram_sent=bool(row["telegram_sent"]),
        telegram_message_id=row["telegram_message_id"],
        status=row["status"],
        scoring=_parse_scoring(row["scoring_json"]),
        proposal=row["proposal"],
        query_used=row["query_used"] or "",
    )


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Keep a persistent connection for in-memory DBs.
        self._conn: sqlite3.Connection | None = None
        if path == ":memory:":
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        self.init()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            if self._conn is not None:
                yield self._conn
                return
            conn = sqlite3.connect(self.path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    normalized_url TEXT NOT NULL UNIQUE,
                    content_hash TEXT NOT NULL,
                    platform TEXT,
                    title TEXT,
                    snippet TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    score REAL,
                    telegram_sent INTEGER NOT NULL DEFAULT 0,
                    telegram_message_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'new',
                    scoring_json TEXT,
                    proposal TEXT,
                    query_used TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_opps_hash ON opportunities(content_hash);
                CREATE INDEX IF NOT EXISTS idx_opps_status ON opportunities(status);
                CREATE INDEX IF NOT EXISTS idx_opps_score ON opportunities(score);
                CREATE INDEX IF NOT EXISTS idx_opps_first_seen ON opportunities(first_seen);

                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    results_found INTEGER DEFAULT 0,
                    new_saved INTEGER DEFAULT 0,
                    qualified INTEGER DEFAULT 0,
                    notified INTEGER DEFAULT 0,
                    error TEXT
                );
                """
            )
            if self._conn is not None:
                self._conn.commit()

    def find_duplicate(self, normalized_url: str, content_hash: str) -> Opportunity | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM opportunities
                WHERE normalized_url = ? OR content_hash = ?
                LIMIT 1
                """,
                (normalized_url, content_hash),
            ).fetchone()
        return _row_to_opportunity(row) if row else None

    def insert_new(
        self,
        *,
        url: str,
        normalized_url: str,
        content_hash: str,
        platform: str,
        title: str,
        snippet: str,
        query_used: str,
    ) -> Opportunity:
        now = _now_iso()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO opportunities (
                    url, normalized_url, content_hash, platform, title, snippet,
                    first_seen, last_seen, status, query_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
                """,
                (url, normalized_url, content_hash, platform, title, snippet, now, now, query_used),
            )
            opp_id = cur.lastrowid
            if self._conn is not None:
                conn.commit()
        found = self.get(opp_id) if opp_id is not None else None
        if found is None:
            raise RuntimeError("failed to insert opportunity")
        return found

    def get(self, opp_id: int) -> Opportunity | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
        return _row_to_opportunity(row) if row else None

    def save_score(self, opp_id: int, scoring: OpportunityScore) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE opportunities
                SET score = ?, scoring_json = ?, title = ?, status = 'scored', last_seen = ?
                WHERE id = ?
                """,
                (scoring.score, scoring.model_dump_json(), scoring.title, _now_iso(), opp_id),
            )
            if self._conn is not None:
                conn.commit()

    def mark_sent(self, opp_id: int, message_id: int | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE opportunities
                SET telegram_sent = 1, telegram_message_id = ?, status = 'sent', last_seen = ?
                WHERE id = ?
                """,
                (message_id, _now_iso(), opp_id),
            )
            if self._conn is not None:
                conn.commit()

    def set_status(self, opp_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE opportunities SET status = ?, last_seen = ? WHERE id = ?",
                (status, _now_iso(), opp_id),
            )
            if self._conn is not None:
                conn.commit()

    def save_proposal(self, opp_id: int, proposal: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE opportunities SET proposal = ?, last_seen = ? WHERE id = ?",
                (proposal, _now_iso(), opp_id),
            )
            if self._conn is not None:
                conn.commit()

    def latest_qualified(self, min_score: float, limit: int = 5) -> list[Opportunity]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM opportunities
                WHERE score >= ? AND status != 'discarded'
                ORDER BY score DESC, first_seen DESC
                LIMIT ?
                """,
                (min_score, limit),
            ).fetchall()
        return [_row_to_opportunity(r) for r in rows]

    def unsent_qualified(self, min_score: float) -> list[Opportunity]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM opportunities
                WHERE score >= ? AND telegram_sent = 0 AND status NOT IN ('discarded', 'applied')
                ORDER BY score DESC
                """,
                (min_score,),
            ).fetchall()
        return [_row_to_opportunity(r) for r in rows]

    def stats(self, since_iso: str | None = None) -> dict[str, int]:
        today = since_iso or datetime.now(timezone.utc).date().isoformat()
        day_like = f"{today}%"
        with self.connect() as conn:
            scanned = conn.execute(
                "SELECT COUNT(*) FROM opportunities WHERE first_seen LIKE ?",
                (day_like,),
            ).fetchone()[0]
            qualified = conn.execute(
                "SELECT COUNT(*) FROM opportunities WHERE first_seen LIKE ? AND score >= 8",
                (day_like,),
            ).fetchone()[0]
            sent = conn.execute(
                "SELECT COUNT(*) FROM opportunities WHERE first_seen LIKE ? AND telegram_sent = 1",
                (day_like,),
            ).fetchone()[0]
            applied = conn.execute(
                "SELECT COUNT(*) FROM opportunities WHERE status = 'applied'"
            ).fetchone()[0]
            discarded = conn.execute(
                "SELECT COUNT(*) FROM opportunities WHERE status = 'discarded'"
            ).fetchone()[0]
        return {
            "scanned_today": scanned,
            "qualified": qualified,
            "sent": sent,
            "applied": applied,
            "discarded": discarded,
        }

    def record_scan(self, summary: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO scans (
                    started_at, finished_at, results_found, new_saved, qualified, notified, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary["started_at"],
                    summary.get("finished_at"),
                    summary.get("results_found", 0),
                    summary.get("new_saved", 0),
                    summary.get("qualified", 0),
                    summary.get("notified", 0),
                    summary.get("error"),
                ),
            )
            if self._conn is not None:
                conn.commit()
