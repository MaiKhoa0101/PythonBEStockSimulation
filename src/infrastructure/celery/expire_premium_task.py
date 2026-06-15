from redis import Redis as SyncRedis
from src.infrastructure.database.models.users.user_model import UserModel
from src.infrastructure.database.models.movies.movie_model import EpisodeModel, MovieModel
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.celery.celery_app import celery_instance
from datetime import datetime


@celery_instance.task(name="tasks.expire_premium_users")
def expire_premium_users():
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        expired_users = db.query(UserModel).filter(
            UserModel.role == "premium",
            UserModel.premium_until < now
        ).all()

        if not expired_users:
            print("[Expire Premium] Không có user nào hết hạn")
            return

        for user in expired_users:
            user.role = "user"

        db.commit()
        print(f"[Expire Premium] Đã thu hồi {len(expired_users)} tài khoản")

    except Exception as e:
        db.rollback()
        print(f"[Expire Premium] Lỗi: {e}")
    finally:
        db.close()