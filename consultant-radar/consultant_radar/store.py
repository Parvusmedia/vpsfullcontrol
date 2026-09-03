from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    uid TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    posted_at TEXT NOT NULL DEFAULT '',
    brands TEXT NOT NULL DEFAULT '[]',
    matched_keywords TEXT NOT NULL DEFAULT '[]',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    first_scan_id INTEGER,
    last_scan_id INTEGER,
    raw_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    jobs_seen INTEGER NOT NULL DEFAULT 0,
    jobs_matched INTEGER NOT NULL DEFAULT 0,
    jobs_new INTEGER NOT NULL DEFAULT 0
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def start_scan(self) -> int:
        cur = self.conn.execute(
            "INSERT INTO scans (started_at) VALUES (?)",
            (utcnow(),),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_scan(self, scan_id: int, *, seen: int, matched: int, new: int) -> None:
        self.conn.execute(
            """
            UPDATE scans
            SET finished_at = ?, jobs_seen = ?, jobs_matched = ?, jobs_new = ?
            WHERE id = ?
            """,
            (utcnow(), seen, matched, new, scan_id),
        )
        self.conn.commit()

    def upsert_jobs(
        self,
        scan_id: int,
        rows: Iterable[tuple[Job, list[str]]],
        now: str | None = None,
    ) -> dict[str, int]:
        stamp = now or utcnow()
        seen = 0
        new = 0
        for job, keywords in rows:
            seen += 1
            existing = self.conn.execute(
                "SELECT uid FROM jobs WHERE uid = ?",
                (job.uid,),
            ).fetchone()
            brands_json = json.dumps(list(job.brands), ensure_ascii=False)
            keywords_json = json.dumps(keywords, ensure_ascii=False)
            raw_json = json.dumps(job.raw, ensure_ascii=False, default=str)
            if existing:
                self.conn.execute(
                    """
                    UPDATE jobs SET
                        company_name = ?,
                        title = ?,
                        location = ?,
                        url = ?,
                        posted_at = ?,
                        brands = ?,
                        matched_keywords = ?,
                        last_seen_at = ?,
                        last_scan_id = ?,
                        raw_json = ?
                    WHERE uid = ?
                    """,
                    (
                        job.company_name,
                        job.title,
                        job.location,
                        job.url,
                        job.posted_at,
                        brands_json,
                        keywords_json,
                        stamp,
                        scan_id,
                        raw_json,
                        job.uid,
                    ),
                )
            else:
                new += 1
                self.conn.execute(
                    """
                    INSERT INTO jobs (
                        uid, company_id, company_name, source, source_id,
                        title, location, url, posted_at, brands, matched_keywords,
                        first_seen_at, last_seen_at, first_scan_id, last_scan_id, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.uid,
                        job.company_id,
                        job.company_name,
                        job.source,
                        job.source_id,
                        job.title,
                        job.location,
                        job.url,
                        job.posted_at,
                        brands_json,
                        keywords_json,
                        stamp,
                        stamp,
                        scan_id,
                        scan_id,
                        raw_json,
                    ),
                )
        self.conn.commit()
        return {"seen": seen, "new": new}

    def list_jobs(
        self,
        *,
        company_id: str | None = None,
        only_new: bool = False,
        scan_id: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        clauses = []
        args: list[Any] = []
        if company_id:
            clauses.append("company_id = ?")
            args.append(company_id)
        if only_new and scan_id is not None:
            clauses.append("first_scan_id = ?")
            args.append(scan_id)
        elif only_new:
            clauses.append("first_scan_id = last_scan_id")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        args.append(limit)
        rows = self.conn.execute(
            f"""
            SELECT uid, company_id, company_name, source, title, location, url,
                   posted_at, brands, matched_keywords, first_seen_at, last_seen_at
            FROM jobs
            {where}
            ORDER BY company_name ASC, title ASC, last_seen_at DESC
            LIMIT ?
            """,
            args,
        ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["brands"] = json.loads(item["brands"] or "[]")
            item["matched_keywords"] = json.loads(item["matched_keywords"] or "[]")
            out.append(item)
        return out
