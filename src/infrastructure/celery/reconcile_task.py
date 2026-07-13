# src/infrastructure/celery/reconcile_task.py

import logging
import os
from datetime import datetime, timedelta, timezone

from redis import Redis as SyncRedis

from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.celery.signal import _session_ctx
from src.infrastructure.database.models.movies.movie_model import MovieModel
from src.infrastructure.elasticsearch.es_client import es_client, MOVIE_INDEX

logger = logging.getLogger(__name__)

# SyncRedis trỏ đúng db=1 (cache) — tách khỏi broker db=0
_redis = SyncRedis.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/1"),
    decode_responses=True,
)


@celery_instance.task(name="tasks.reconcile_movie_data")
def task_reconcile_movie_data():
    logger.info("[Đối soát] Bắt đầu tiến trình rà soát dữ liệu phim biến động...")

    now                   = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)

    try:
        with _session_ctx() as session:
            recent_movies = session.query(MovieModel).filter(
                MovieModel.updated_at >= twenty_four_hours_ago,
                MovieModel.is_deleted == False,
            ).all()

            # Trích dữ liệu cần dùng ra plain dict NGAY TRONG khối `with`, trước khi
            # session đóng — tránh DetachedInstanceError khi truy cập attribute của
            # MovieModel ở vòng lặp bên dưới (lúc đó session đã đóng, attribute bị expire).
            movies_data = [
                {"id": m.id, "updated_at": m.updated_at, "slug_name": m.slug_name}
                for m in recent_movies
            ]

        logger.info("[Đối soát] Tìm thấy %d phim biến động trong 24h.", len(movies_data))

        if not movies_data:
            return

        for movie in movies_data:

            # ── KHÂU 1: ĐỐI SOÁT ELASTICSEARCH ──────────────────────────────
            need_sync_es = False
            try:
                es_res        = es_client.get(index=MOVIE_INDEX, id=str(movie["id"]))
                es_updated_at = es_res["_source"].get("updated_at")

                if not es_updated_at or es_updated_at < movie["updated_at"].isoformat():
                    need_sync_es = True
                    logger.warning("❌ [Lệch pha ES] Phim %s — ES cũ hơn DB.", movie["id"])
            except Exception:
                need_sync_es = True
                logger.warning("❌ [Thiếu ES] Phim %s chưa có trên ES.", movie["id"])

            if need_sync_es:
                celery_instance.send_task(
                    "tasks.sync_movie_to_es",
                    args=[movie["id"]],
                    queue="light_queue",
                )
                logger.info("[Đã vá ES] Phát lệnh sync cho phim %s.", movie["id"])

            # ── KHÂU 2: ĐỐI SOÁT REDIS CACHE ────────────────────────────────
            cache_key = f"movie:detail:{movie['slug_name']}"

            if _redis.exists(cache_key):
                _redis.delete(cache_key)
                logger.warning("🧹 [Đã vá Cache] Xóa cache thối: %s", cache_key)

    except Exception:
        logger.exception("💥 Lỗi hệ thống trong tiến trình đối soát.")