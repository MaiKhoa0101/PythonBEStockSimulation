import os

from redis import Redis as SyncRedis
from src.infrastructure.database.models.movies.movie_model import EpisodeModel, MovieModel
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.celery.celery_app import celery_instance


@celery_instance.task(
    name="tasks.sync_view_count",
    queue = "light_queue"
)
def sync_view_count():
    redis_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    r = SyncRedis.from_url(redis_url, decode_responses=True)
    db = SessionLocal()

    try:
        keys = r.keys("view:*")
        if not keys:
            print("[Sync View] Không có view nào cần sync")
            return

        for key in keys:
            movie_id = key.split(":")[1]
            count = r.getdel(key)
            if count:
                db.query(MovieModel).filter(
                    MovieModel.id == movie_id
                ).update({MovieModel.view: MovieModel.view + int(count)})

        db.commit()
        print(f"[Sync View] Đã sync view cho {len(keys)} phim")

    except Exception as e:
        db.rollback()
        print(f"[Sync View] Lỗi: {e}")
    finally:
        db.close()
        r.close()