"""APScheduler integration for periodic alert generation."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.services.alert_service import generate_alerts


scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler() -> BackgroundScheduler:
    """Start the background scheduler once per process."""
    if scheduler.running:
        return scheduler

    scheduler.add_job(
        generate_alerts,
        trigger=IntervalTrigger(minutes=settings.ALERT_CHECK_INTERVAL_MINUTES),
        id="deadline_alert_generator",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    return scheduler


def shutdown_scheduler() -> None:
    """Stop the background scheduler on shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
