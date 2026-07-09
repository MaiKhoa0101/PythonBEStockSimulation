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
from datetime import datetime, timedelta, timezone

import redis
from sqlalchemy import func
from elasticsearch.helpers import bulk  # 🔥 THÊM: Import helper bulk để đẩy mẻ lớn tốc độ cao

from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.database.models.movies.movie_model import MovieModel
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.elasticsearch.es_client import es_client  # 🔥 THÊM: Sử dụng es_client chung

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
      2. Pipeline Redis INCRBY — tăng view và like ảo phục vụ xả đệm MySQL.
      3. Bulk đúc dữ liệu tương tác thô (view/like) của NGÀY HÔM QUA ném vào Elasticsearch.
    """

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

    # ── Bước 3: Hạ tầng nạp dữ liệu song song (Redis + Elasticsearch) ──────────
    total_views = 0
    total_likes = 0
    es_actions = []  # Mảng chứa danh sách các tài liệu log thô chuẩn bị bắn sang ES

    # 💡 CHI TIẾT VÀNG: Bốc mốc thời gian ngày hôm qua để con task tổng hợp 
    # (chạy 5 phút/lần khi test) bốc được số liệu để tính toán ngay lập tức.
    now = datetime.now(timezone.utc)
    yesterday_base = now - timedelta(days=1)

    try:
        pipe = _redis.pipeline(transaction=False)

        for movie in picked:
            n_views = random.randint(VIEW_MIN, VIEW_MAX)
            n_likes = random.randint(LIKE_MIN, LIKE_MAX)

            # 🛠️ Hành động 1: Tích lũy vào RAM Redis db=1 phục vụ luồng xả đệm MySQL cũ
            pipe.incrby(f"view:{movie.id}", n_views)
            pipe.incrby(f"like:{movie.id}", n_likes)

            total_views += n_views
            total_likes += n_likes

            # 🛠️ Hành động 2: Chuẩn bị mẻ log thô ném sang Elasticsearch
            # Tạo các bản ghi sự kiện View
            for _ in range(n_views):
                # Sinh giờ, phút, giây ngẫu nhiên trong ngày hôm qua để biểu đồ miền/đường uốn lượn tự nhiên
                h = random.randint(0, 23)
                m = random.randint(0, 59)
                s = random.randint(0, 59)
                ts = datetime(yesterday_base.year, yesterday_base.month, yesterday_base.day, h, m, s, tzinfo=timezone.utc)
                
                es_actions.append({
                    "_index": "movie_interactions_log",
                    "_source": {
                        "movie_id": str(movie.id),
                        "action": "view",
                        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S") # Định dạng khớp strict_date_hour_minute_second
                    }
                })

            # Tạo các bản ghi sự kiện Like
            for _ in range(n_likes):
                h = random.randint(0, 23)
                m = random.randint(0, 59)
                s = random.randint(0, 59)
                ts = datetime(yesterday_base.year, yesterday_base.month, yesterday_base.day, h, m, s, tzinfo=timezone.utc)
                
                es_actions.append({
                    "_index": "movie_interactions_log",
                    "_source": {
                        "movie_id": str(movie.id),
                        "action": "like",
                        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                })

        # Thực thi đẩy bộ đếm sang Redis (1 Round-trip)
        pipe.execute()

        # 🚀 Tiến hành thực thi đẩy mẻ log thô sang Elasticsearch
        if es_actions:
            success_count, failed = bulk(es_client, es_actions)
            logger.info("[SimTraffic] Đã bulk sync thành công %d tài liệu log thô vào Elasticsearch Index 'movie_interactions_log' ✓", success_count)
            if failed:
                logger.error("[SimTraffic] Số bản ghi bulk thất bại: %d", len(failed))

    except Exception as exc:
        logger.exception("[SimTraffic] Hệ thống đường ống (Pipeline) gặp lỗi: %s", exc)
        raise self.retry(exc=exc)

    result = {
        "picked":      len(picked),
        "views_added": total_views,
        "likes_added": total_likes,
        "movies":      [m.name for m in picked],
    }
    logger.info("[SimTraffic] Hoàn tất chu kỳ giả lập: %s", result)
    return result