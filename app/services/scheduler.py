"""
Wraps APScheduler's AsyncIOScheduler to call the checker service
at a configurable interval while the FastAPI app is running.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.config import settings
from app.services.checker import run_checks

_scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Register the monitoring job and start the scheduler."""
    interval = settings.monitoring_interval_seconds
    _scheduler.add_job(
        run_checks,
        trigger="interval",
        seconds=interval,
        id="node_checker",
        replace_existing=True,
        max_instances=1,        # prevent overlapping runs
        misfire_grace_time=10,
    )
    _scheduler.start()
    logger.info("Scheduler started — checking nodes every {} s.", interval)


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler on app exit."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
