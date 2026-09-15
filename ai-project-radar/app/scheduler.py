from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import Settings
from app.pipeline import Pipeline

logger = logging.getLogger(__name__)


def build_scheduler(pipeline: Pipeline, settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    hours = max(1, settings.scan_interval_hours)
    scheduler.add_job(
        pipeline.run,
        "interval",
        hours=hours,
        id="hourly_radar_scan",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info("Scheduled radar scan every %s hour(s)", hours)
    return scheduler
