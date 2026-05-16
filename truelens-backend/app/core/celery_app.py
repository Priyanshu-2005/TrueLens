import os
from celery import Celery

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "truelens_worker",
    broker=REDIS_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks.ml_pipeline"]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300, # 5 min limit for ML tasks
    task_always_eager=True, # Run synchronously for testing without Redis
)
