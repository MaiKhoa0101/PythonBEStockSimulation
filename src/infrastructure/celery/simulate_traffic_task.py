# src/infrastructure/celery/simulate_traffic_task.py
"""
Task giả lập traffic người dùng để kiểm thử Dashboard Analytics.

Tại sao bơm vào Redis thay vì ghi thẳng MySQL/PostgreSQL?
─────────────────────────────────────────────────────────
  MySQL INCRBY trực tiếp       Redis INCRBY
  ──────────────────────────   ──────────────────────────────
  SELECT + UPDATE + COMMIT     INCRBY — 1 lệnh, ~0.1ms
  ~5–20ms / ghi                Lock-free, không blocking
  Row lock khi nhiều task      Atomic tự nhiên
  Không chịu được traffic spike Hấp thụ spike tốt

  → Pattern Write-Behind Buffer:
    Redis gom counter trong RAM.
    Task sync_view_count (đã có, chạy mỗi 5 phút)
    định kỳ flush toàn bộ counter xuống MySQL.
    Dashboard đọc từ MySQL sau flush.
"""

import logging
import os
import random

import redis
from sqlalchemy import func

from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.database.models.movies.movie_model import MovieModel
from src.infrastructure.database.session import SessionLocal

logger = logging.getLogger(__name__)

# ── Redis sync client (db=1, tách biệt khỏi Celery broker db=0) ──────────────
_redis = redis.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/1"),
    decode_responses=True,
)

POOL_SIZE = 20   
PICK_MIN  = 5
PICK_MAX  = 10
VIEW_MIN  = 10
VIEW_MAX  = 50
LIKE_MIN  = 1
LIKE_MAX  = 5


@celery_instance.task(
    bind=True,
    name="tasks.simulate_user_traffic",
    max_retries=2,
    default_retry_delay=60,
    queue="light_queue",
    acks_late=True,
)
def task_simulate_user_traffic(self):
    """
    Mỗi 5 phút:
      1. Bốc ngẫu nhiên 5–10 phim đang hoạt động từ MySQL.
      2. Pipeline Redis INCRBY — tăng view và like ảo.
      3. sync_view_count task (cũ) sẽ flush Redis → MySQL định kỳ.
    """

    # ── Bước 1: Lấy pool phim ngẫu nhiên từ MySQL ────────────────────────────
    db = SessionLocal()
    try:
        movies = (
            db.query(MovieModel.id, MovieModel.name)
            .filter(MovieModel.is_deleted == False)
            .order_by(func.rand())          # MySQL: RAND(); PostgreSQL: RANDOM()
            .limit(POOL_SIZE)
            .all()
        )
    except Exception as exc:
        logger.exception("[SimTraffic] Lỗi query MySQL: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()

    if not movies:
        logger.warning("[SimTraffic] Không có phim hoạt động — bỏ qua")
        return {"picked": 0, "views_added": 0, "likes_added": 0}

    # ── Bước 2: Sample 5–10 phim từ pool ─────────────────────────────────────
    k      = random.randint(PICK_MIN, PICK_MAX)
    picked = random.sample(movies, min(k, len(movies)))

    # ── Bước 3: Redis pipeline — 1 round-trip cho tất cả INCRBY ──────────────
    # pipeline(transaction=False): không dùng MULTI/EXEC, đủ dùng cho INCRBY
    # vì từng lệnh INCRBY đã atomic tự nhiên trong Redis
    total_views = 0
    total_likes = 0

    try:
        pipe = _redis.pipeline(transaction=False)

        for movie in picked:
            n_views = random.randint(VIEW_MIN, VIEW_MAX)
            n_likes = random.randint(LIKE_MIN, LIKE_MAX)

            pipe.incrby(f"view:{movie.id}", n_views)
            pipe.incrby(f"like:{movie.id}", n_likes)

            total_views += n_views
            total_likes += n_likes

        pipe.execute()

    except Exception as exc:
        logger.exception("[SimTraffic] Redis pipeline lỗi: %s", exc)
        raise self.retry(exc=exc)

    result = {
        "picked":      len(picked),
        "views_added": total_views,
        "likes_added": total_likes,
        "movies":      [m.name for m in picked],
    }
    logger.info("[SimTraffic] ✓ %s", result)
    return result