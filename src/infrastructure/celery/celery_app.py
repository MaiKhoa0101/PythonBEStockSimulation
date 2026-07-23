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
        "src.infrastructure.celery.hls_task",
        "src.infrastructure.celery.view_count_task",
        "src.infrastructure.celery.expire_premium_task",   
        "src.infrastructure.celery.elastic_task_movie",
        "src.infrastructure.celery.reconcile_task",
        "src.infrastructure.celery.aggregate_task",
        "src.infrastructure.celery.simulate_traffic_task",
        "src.infrastructure.celery.sync_movie_task",
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
            "schedule": 400.0, 
        },
        "expire-premium-users": {
            "task": "tasks.expire_premium_users",
            "schedule": 3000.0,  
        },
        "reconcile-db-to-es-every-night": {
            "task": "tasks.reconcile_movie_data",
            "schedule": 300, # crontab(hour=16, minute=7),
            "options": {"queue": "light_queue"} 
        },
        "aggregate-es-to-postgres-daily": {
            "task":     "tasks.aggregate_es_to_postgres",
            "schedule": 300, 
            "kwargs":   {"days_back": 1}, 
            "options":  {"queue": "light_queue"},
        },
        "simulate-user-traffic-every-5min": {
            "task":     "tasks.simulate_user_traffic",
            "schedule": 900.0,  
            "kwargs":   {"days_back": 1},  
            "options":  {"queue": "light_queue"},
        },
        "sync-movies-from-external-every-5min": {
            "task":     "tasks.sync_movies_from_external",
            "schedule": 2000.0,
            "options":  {"queue": "heavy_queue"},
        },
    }
)
import src.infrastructure.celery.signal


# # ── Kích hoạt backfill 1 lần khi Celery Beat khởi động ───────────────────────
# @beat_init.connect
# def _trigger_one_time_backfill(**kwargs):
#     """
#     Chạy đúng 1 lần khi tiến trình Celery Beat khởi động, CHỈ KHI
#     BACKFILL_DAYS_BACK > 1. Dùng chain() để đảm bảo simulate_traffic
#     (bơm dữ liệu giả vào ES) chạy xong hẳn rồi mới tới aggregate
#     (tổng hợp ES → Postgres) — không cần gọi tay qua terminal.

#     File lock /tmp/.backfill_lock_<N> đảm bảo nếu Beat bị restart nhiều
#     lần (crash loop, deploy lại...) trong lúc quên xoá biến môi trường,
#     backfill cũng không bị bơm lặp lại dữ liệu.
#     """
#     if BACKFILL_DAYS_BACK <= 1:
#         return

#     if os.path.exists(_BACKFILL_LOCK_FILE):
#         logger.info(
#             "[Backfill] Đã backfill %d ngày trước đó rồi (thấy lock file %s) — bỏ qua.",
#             BACKFILL_DAYS_BACK, _BACKFILL_LOCK_FILE,
#         )
#         return

#     # Import trễ (lazy import) để tránh circular import, vì 2 task module
#     # này tự import ngược lại `celery_instance` từ chính file này.
#     from src.infrastructure.celery.simulate_traffic_task import task_simulate_user_traffic
#     from src.infrastructure.celery.aggregate_task import task_aggregate_es_to_postgres

#     logger.warning(
#         "[Backfill] BACKFILL_DAYS_BACK=%d — kích hoạt chuỗi backfill: "
#         "simulate_traffic → aggregate_es_to_postgres. "
#         "Nhớ đặt lại BACKFILL_DAYS_BACK=1 sau khi hoàn tất!",
#         BACKFILL_DAYS_BACK,
#     )

#     # .si() = "immutable signature" — KHÔNG truyền kết quả trả về của task
#     # trước làm tham số cho task sau (2 task nhận days_back cố định, không
#     # liên quan gì tới nhau về mặt dữ liệu trả về).
#     chain(
#         task_simulate_user_traffic.si(days_back=BACKFILL_DAYS_BACK),
#         task_aggregate_es_to_postgres.si(days_back=BACKFILL_DAYS_BACK),
#     ).apply_async()

#     try:
#         with open(_BACKFILL_LOCK_FILE, "w") as f:
#             f.write("done")
#     except OSError:
#         logger.exception("[Backfill] Không ghi được lock file %s", _BACKFILL_LOCK_FILE)