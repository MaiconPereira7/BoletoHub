from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "boletohub",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    beat_schedule={
        "scan-emails-periodic": {
            "task": "app.tasks.scan_emails_task",
            "schedule": settings.email_scan_interval_minutes * 60,
        },
        "update-overdue-boletos-daily": {
            "task": "app.tasks.update_overdue_boletos_task",
            "schedule": crontab(hour=0, minute=0),
        },
    },
)
