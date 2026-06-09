"""Celery application factory for background tasks."""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "neomuse",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Ensure task modules are imported so Celery can register them.
celery_app.autodiscover_tasks(["app.services"])

# Explicit import to register tasks when worker starts.
from app.services import report_service  # noqa: E402,F401
