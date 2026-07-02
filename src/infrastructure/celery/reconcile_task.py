import logging
from datetime import datetime, timedelta, timezone
import os
from src.infrastructure.elasticsearch.es_client import es_client
from src.infrastructure.database.models.movies.movie_model import MovieModel
from src.infrastructure.celery.signal import _session_ctx
from src.infrastructure.celery.celery_app import celery_instance
from redis import Redis as SyncRedis

from fastapi_cache import FastAPICache

logger = logging.getLogger(__name__)

async def check_and_evict_redis_cache(cache_key: str) -> bool:
    redis_backend = FastAPICache.get_backend()
    
    cache_exists = await redis_backend.get(cache_key)
    if cache_exists:
        await redis_backend.clear(key=cache_key)
        return True
    return False

@celery_instance.task(name="tasks.reconcile_movie_data")
def task_reconcile_movie_data():
    logger.info("[Đối soát] Bắt đầu tiến trình rà soát dữ liệu phim biến động...")
    redis_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    r = SyncRedis.from_url(redis_url, decode_responses=True)

    now = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)

    try:
        with _session_ctx() as session:
            recent_movies = session.query(MovieModel).filter(
                MovieModel.updated_at >= twenty_four_hours_ago,
                MovieModel.is_deleted == False
            ).all()
            
            logger.info(f"[Đối soát] Tìm thấy {len(recent_movies)} phim có biến động trong 24h qua.")
            
            redis_backend = FastAPICache.get_backend()
            
            for movie in recent_movies:
                # ── KHÂU 1: ĐỐI SOÁT ELASTICSEARCH ─────────────────────────────────────
                need_sync_es = False
                try:
                    # Lấy trực tiếp document từ ES bằng ID gốc của MySQL
                    es_res = es_client.get(index=es_client.MOVIE_INDEX, id=str(movie.id))
                    es_source = es_res["_source"]
                    
                    es_updated_at = es_source.get("updated_at")
                    if not es_updated_at or es_updated_at < movie.updated_at.isoformat():
                        need_sync_es = True
                        logger.warning(f"❌ [Lệch pha ES] Phim ID {movie.id} dữ liệu ES bị cũ.")
                except Exception:
                    need_sync_es = True
                    logger.warning(f"❌ [Thiếu dữ liệu ES] Phim ID {movie.id} chưa tồn tại trên ES.")

                # Nếu phát hiện lệch pha hoặc thiếu -> Bắn lệnh vá sang Celery Sync Task
                if need_sync_es:
                    celery_instance.send_task("tasks.sync_movie_to_es", args=[movie.id], queue="light_queue")
                    logger.info(f"[Đã vá ES] Phát lệnh tái đồng bộ cho phim ID {movie.id}")

                # ── KHÂU 2: ĐỐI SOÁT REDIS CACHE ──────────────────────────────────────
                # Tư tưởng luồng Ghi: Nếu phim có biến động, Cache CHI TIẾT bắt buộc phải TRỐNG
                # Nếu giờ này kiểm tra mà vẫn thấy Key Cache tồn tại -> Nghĩa là luồng xóa cache lúc ghi bị lỗi (Cache thối)
                cache_key = f"movie:detail:{movie.slug_name}"
                
                # Kiểm tra ngầm sự tồn tại của key trên Redis
                cache_exists = redis_backend.get(cache_key)
                if cache_exists:
                    # Tiến hành vá: Ép xóa sạch cái cache thối này đi
                    redis_backend.clear(cache_key)
                    logger.warning(f"🧹 [Đã vá Cache] Phát hiện và dọn dẹp Cache thối tại Key: {cache_key}")
                    
    except Exception as e:
        logger.error(f"💥 Lỗi hệ thống trong quá trình chạy đối soát: {str(e)}")