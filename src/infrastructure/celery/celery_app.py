import logging
import os

from celery import Celery, chain
from celery.schedules import crontab
from celery.signals import beat_init

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

logger = logging.getLogger(__name__)

BACKFILL_DAYS_BACK = int(os.getenv("BACKFILL_DAYS_BACK", "1"))

celery_instance = Celery(
    "movie_streaming_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "src.infrastructure.celery.calculate_item_similarity_task",
        "src.infrastructure.celery.hls_task",
        "src.infrastructure.celery.view_count_task",
        "src.infrastructure.celery.expire_premium_task",   
        "src.infrastructure.celery.elastic_task_movie",
        "src.infrastructure.celery.reconcile_task",
        "src.infrastructure.celery.aggregate_task",
        "src.infrastructure.celery.simulate_traffic_task",
        "src.infrastructure.celery.sync_movie_task",
        "src.infrastructure.celery.view_log_task"
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
            "schedule": 3000.0,  
        },
        "reconcile-db-to-es-every-night": {
            "task": "tasks.reconcile_movie_data",
            "schedule": crontab(hour=16, minute=7),
            "options": {"queue": "light_queue"} 
        },
        "aggregate-es-to-postgres-daily": {
            "task":     "tasks.aggregate_es_to_postgres",
            "schedule": 3600, 
            "kwargs":   {"days_back": 1}, 
            "options":  {"queue": "light_queue"},
        },
        "simulate-user-traffic-every-5min": {
            "task":     "tasks.simulate_user_traffic",
            "schedule": 300.0,  
            "kwargs":   {"days_back": 180},  
            "options":  {"queue": "light_queue"},
        },
        # "sync-movies-from-external-every-5min": {
        #     "task":     "tasks.sync_movies_from_external",
        #     "schedule": 2000.0,
        #     "options":  {"queue": "heavy_queue"},
        # },
        "flush-view-logs-buffer-every-30s": {
            "task": "tasks.flush_view_logs_buffer",
            "schedule": 3600.0,
            "options": {"queue": "light_queue"},
        },
        "calculate-item-similarity-every-6h": {
            "task": "tasks.calculate_item_similarity",
            "schedule": crontab(minute=0, hour=2),
            "options": {"queue": "heavy_queue"},
        },
    }
)
import src.infrastructure.celery.signal



_BACKFILL_LOCK_FILE = "/tmp/.sync_movies_backfill_done"
@beat_init.connect
def _trigger_one_time_backfill(**kwargs):
    if os.path.exists(_BACKFILL_LOCK_FILE):
        logger.info(
            "[Backfill] Đã chạy sync_movies_from_external trước đó rồi "
            "(thấy lock file %s) — bỏ qua.", _BACKFILL_LOCK_FILE,
        )

    from src.infrastructure.celery.sync_movie_task import sync_movies_from_external

    sync_movies_from_external.si().apply_async()

    try:
        with open(_BACKFILL_LOCK_FILE, "w") as f:
            f.write("done")
    except OSError:
        logger.exception("[Backfill] Không ghi được lock file %s", _BACKFILL_LOCK_FILE)