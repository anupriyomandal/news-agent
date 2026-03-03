from __future__ import annotations

from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler

from .config import INGEST_INTERVAL_MINUTES


def build_scheduler(ingest_job: Callable[[], None]) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        func=ingest_job,
        trigger="interval",
        minutes=INGEST_INTERVAL_MINUTES,
        id="rss_ingestion_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
