import os
from celery.schedules import crontab
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
        "src.infrastructure.celery.elastic_task_movie",
        "src.infrastructure.celery.reconcile_task",
        "src.infrastructure.celery.aggregate_task",
        "src.infrastructure.celery.simulate_traffic_task"
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
            "schedule": 3600.0, 
        },
        "expire-premium-users": {
            "task": "tasks.expire_premium_users",
            "schedule": 3600.0,  
        },
        "reconcile-db-to-es-every-night": {
            "task": "tasks.reconcile_movie_data",
            "schedule": 3600, # crontab(hour=16, minute=7),
            "options": {"queue": "light_queue"} 
        },
        "aggregate-es-to-postgres-daily": {
            "task":     "tasks.aggregate_es_to_postgres",
            "schedule": crontab(hour=1, minute=0),  # 01:00 sáng mỗi ngày
            "options":  {"queue": "light_queue"},
        },
        "simulate-user-traffic-every-5min": {
            "task":     "tasks.simulate_user_traffic",
            "schedule": 300.0,                    # 300 giây = 5 phút
            "options":  {"queue": "light_queue"},
        },        
    }
)
import src.infrastructure.celery.signal