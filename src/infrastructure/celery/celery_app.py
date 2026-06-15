import os

from celery import Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

celery_instance = Celery(
    "movie_streaming_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "src.infrastructure.celery.hls_task",
        "src.infrastructure.celery.view_count_task",
        "src.infrastructure.celery.expire_premium_task",    
    ])

celery_instance.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    beat_schedule={
        "sync-view-count": {
            "task": "tasks.sync_view_count",
            "schedule": 300.0, 
        },
        "expire-premium-users": {
            "task": "tasks.expire_premium_users",
            "schedule": 30.0,  
        }
    }
)