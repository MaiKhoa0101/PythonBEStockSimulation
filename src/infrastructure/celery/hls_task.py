import os
import ffmpeg
from redis import Redis as SyncRedis
from src.infrastructure.database.models.movies.movie_model import EpisodeModel, MovieModel
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.celery.celery_app import celery_instance


def _update_episode_db(episode_id: str, relative_db_path: str) -> bool:
    db = SessionLocal()
    try:
        episode = db.query(EpisodeModel).filter(EpisodeModel.id == episode_id).first()

        if not episode:
            return False

        episode.link_m3u8 = relative_db_path
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"[HLS Task] Lỗi DB: {e}")
        raise
    finally:
        db.close()


@celery_instance.task(
    bind=True,
    name="tasks.process_hls",
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
)
def process_hls_task(
    self,
    temp_path: str,
    target_dir: str,
    episode_id: str,
    relative_db_path: str,
    is_short: bool,
):
    try:
        m3u8_full_path = os.path.join(target_dir, "index.m3u8")
        print(f"[HLS Task] Bắt đầu xử lý: {m3u8_full_path}")

        (
            ffmpeg
            .input(temp_path)
            .output(
                m3u8_full_path,
                format="hls",
                hls_time=10,
                hls_list_size=0,
                c="copy",
            )
            .run(
                overwrite_output=True,
                capture_stdout=True,
                capture_stderr=True,
            )
        )

        print(f"[HLS Task] ffmpeg hoàn thành: {m3u8_full_path}")

        if not is_short:
            is_updated = _update_episode_db(episode_id, relative_db_path)
            if not is_updated:
                print(f"[HLS Task] Không tìm thấy tập {episode_id}")

    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
        print(f"[HLS Task] ffmpeg lỗi:\n{stderr}")
        raise self.retry(exc=exc)

    except Exception as exc:
        print(f"[HLS Task] Lỗi: {exc}")
        raise self.retry(exc=exc)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"[HLS Task] Đã xoá file tạm: {temp_path}")



@celery_instance.task(
    name="tasks.sync_view_count"
)
def sync_view_count():
    redis_url = os.getenv("CELERY_BROKER_URL")
    r = SyncRedis.from_url(redis_url, decode_responses = True)
    db = SessionLocal()

    try:
        keys = r.keys("view:*")
        if not keys:
            return

        for key in keys:
            movie_id = key.split(":")[1]
            count = r.getdel(key)
            if count:
                db.query(MovieModel).filter(
                    MovieModel.id == movie_id
                ).update({MovieModel.view: MovieModel.view + int(count)})
            db.commit()
            print(f"Đã sync view với {len(keys)} phim")
    except Exception as e:
        db.rollback()
        print(f"[Sync View] Lỗi: {e}")
    finally:
        db.close()
        r.close()