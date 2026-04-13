# app/etl/celery_app.py

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "adamas_einvoice_etl",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.etl.tasks.extract",
        "app.etl.tasks.transform",
        "app.etl.tasks.validate",
        "app.etl.tasks.load",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.celery_task_always_eager,
    task_track_started=True,
    task_acks_late=True,             # acknowledge only after task completes — no data loss
    worker_prefetch_multiplier=1,    # one task at a time per worker — critical for invoice integrity
    task_routes={
        "app.etl.tasks.validate.*": {"queue": "validation"},
        "app.etl.tasks.load.*":     {"queue": "load"},
        "app.etl.tasks.extract.*":  {"queue": "default"},
        "app.etl.tasks.transform.*": {"queue": "default"},
    },
    # Retry settings
    task_max_retries=3,
    task_default_retry_delay=5,      # 5 seconds between retries
)
