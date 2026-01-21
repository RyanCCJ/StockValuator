"""Celery application configuration for background tasks."""

from celery import Celery

from src.core.config import get_settings

settings = get_settings()

# Create Celery app instance
celery_app = Celery(
    "stockvaluator",
    broker=settings.celery_broker,
    backend=settings.redis_url,
    include=["src.worker"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    worker_prefetch_multiplier=1,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-price-alerts-every-5-minutes": {
        "task": "src.worker.check_price_alerts_task",
        "schedule": 300.0,  # Every 5 minutes
    },
}
