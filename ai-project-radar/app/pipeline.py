from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.config import Settings
from app.db import Database
from app.models import ScanSummary, SearchResult
from app.normalize import content_hash, detect_platform, normalize_url
from app.proposal.base import ProposalGenerator
from app.scoring.base import Scorer
from app.search.base import SearchProvider
from app.search.queries import generate_queries, select_queries
from app.telegram.bot import TelegramBot

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        settings: Settings,
        db: Database,
        search: SearchProvider,
        scorer: Scorer,
        bot: TelegramBot | None,
        proposal: ProposalGenerator | None = None,
    ) -> None:
        self.settings = settings
        self.db = db
        self.search = search
        self.scorer = scorer
        self.bot = bot
        self.proposal = proposal

    async def run(self) -> ScanSummary:
        started = datetime.now(timezone.utc)
        summary = ScanSummary(started_at=started)
        try:
            results = await self._collect()
            summary.results_found = len(results)
            for result in results:
                created = self._save_if_new(result)
                if created is None:
                    continue
                summary.new_saved += 1
                scoring = await self.scorer.score(result)
                if created.id is None:
                    continue
                self.db.save_score(created.id, scoring)
                created = self.db.get(created.id)
                if created is None or created.scoring is None:
                    continue
                if created.score is not None and created.score >= self.settings.min_notify_score:
                    summary.qualified += 1

            for opp in self.db.unsent_qualified(self.settings.min_notify_score):
                if self.bot is None:
                    continue
                try:
                    message_id = await self.bot.notify_opportunity(opp)
                    if opp.id is not None:
                        self.db.mark_sent(opp.id, message_id)
                    summary.notified += 1
                except Exception:
                    logger.exception("Failed to notify opportunity id=%s", opp.id)

            summary.finished_at = datetime.now(timezone.utc)
            self._persist_summary(summary)
            return summary
        except Exception as exc:
            summary.error = str(exc)
            summary.finished_at = datetime.now(timezone.utc)
            self._persist_summary(summary)
            logger.exception("Scan failed")
            return summary

    async def _collect(self) -> list[SearchResult]:
        queries = select_queries(
            generate_queries(),
            self.settings.queries_per_scan,
        )
        max_age = self.settings.max_age_exceptional_hours
        collected: list[SearchResult] = []
        seen_urls: set[str] = set()
        for query in queries:
            try:
                hits = await self.search.search(query, max_age_hours=max_age)
            except Exception:
                logger.exception("Search failed query=%s", query)
                continue
            for hit in hits:
                key = normalize_url(hit.url)
                if not key or key in seen_urls:
                    continue
                seen_urls.add(key)
                collected.append(hit)
        return collected

    def _save_if_new(self, result: SearchResult):
        url = result.url
        normalized = normalize_url(url)
        hashed = content_hash(url, result.title, result.snippet)
        existing = self.db.find_duplicate(normalized, hashed)
        if existing is not None:
            return None
        return self.db.insert_new(
            url=url,
            normalized_url=normalized,
            content_hash=hashed,
            platform=detect_platform(url) or result.source,
            title=result.title,
            snippet=result.snippet,
            query_used=result.query,
        )

    def _persist_summary(self, summary: ScanSummary) -> None:
        self.db.record_scan(
            {
                "started_at": summary.started_at.isoformat(),
                "finished_at": summary.finished_at.isoformat() if summary.finished_at else None,
                "results_found": summary.results_found,
                "new_saved": summary.new_saved,
                "qualified": summary.qualified,
                "notified": summary.notified,
                "error": summary.error,
            }
        )
