# src/infrastructure/celery/simulate_traffic_task.py
"""
Task giả lập traffic người dùng để kiểm thử Dashboard Analytics VÀ sinh
dữ liệu huấn luyện cho Item-Based Collaborative Filtering.

[... giữ nguyên toàn bộ docstring cũ về Write-Behind Buffer, Backfill ...]

BỔ SUNG MỚI — Smart Mocking & User Clustering (Item-Based CF)
─────────────────────────────────────────────────────────
  Thay vì chọn phim ngẫu nhiên đều (uniform random) cho mỗi lượt view,
  giờ đây việc "user nào xem phim nào" tuân theo quy luật:

    1. Pareto 80/20: 20% số phim trong pool được đánh dấu "Trending".
    2. Mỗi user được gán 1 "gu" (preferred category) CỐ ĐỊNH, xác định
       bằng hash(user_id) — xem simulate_traffic_config.py.
    3. Với mỗi lượt view: 80% khả năng user chọn phim Trending HOẶC đúng
       gu của họ; 20% còn lại chọn ngẫu nhiên phim bất kỳ (nhiễu tự nhiên).
    4. duration_watched tỷ lệ thuận với mức độ "khớp gu": 80-100% thời
       lượng nếu đúng gu/trending, 10-30% nếu trái gu.

  Mục đích: sinh ra dữ liệu view log có QUY LUẬT thay vì nhiễu loạn, để
  calculate_item_similarity_task (Cosine Similarity) học ra được các cụm
  phim tương đồng có ý nghĩa thay vì ma trận toàn nhiễu ngẫu nhiên.
"""

import hashlib
import logging
import os
import random
from datetime import datetime, timedelta, timezone

import redis
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from elasticsearch.helpers import bulk

from src.infrastructure.database.models.movies.movie_model import EpisodeModel, MovieModel
from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.celery.simulate_traffic_config import (
    TRENDING_RATIO,
    PREFERENCE_WEIGHT,
    HIGH_WATCH_RATIO_RANGE,
    LOW_WATCH_RATIO_RANGE,
    ASSUMED_FULL_DURATION_SECONDS,
    get_preferred_category_id,
)
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.elasticsearch.es_client import es_client
from src.infrastructure.database.analytics_session import AnalyticsSessionLocal
from src.infrastructure.database.models.analytics.movie_view_log import MovieViewLogModel

logger = logging.getLogger(__name__)

_redis = redis.from_url(
    os.getenv("REDIS_URL_CACHE"),
    decode_responses=True,
)

POOL_SIZE = 20
PICK_MIN  = 5
PICK_MAX  = 10

VIEW_MIN  = 0
VIEW_MAX  = 500
LIKE_MIN  = 0
LIKE_MAX  = 50

WEEKEND_MULTIPLIER = 2.0

SIMULATED_USER_POOL  = [f"anonymous_{i:03d}" for i in range(1, 1000)]
ANONYMOUS_VIEW_RATIO = 0.2

DURATION_WATCHED_MIN = 30
DURATION_WATCHED_MAX = 7200


def _pick_simulated_user_id() -> str:
    if random.random() < ANONYMOUS_VIEW_RATIO:
        return "anonymous"
    return random.choice(SIMULATED_USER_POOL)


def _pick_movie_for_user(
    movies: list,
    movie_categories: dict[str, list[str]],
    trending_ids: set[str],
    preferred_category_id: str | None,
) -> tuple[object, bool]:
    """
    Trả về (movie, in_preference).
    in_preference=True nếu phim được chọn vì Trending hoặc đúng "gu" —
    dùng để quyết định duration_watched ở bước sau.
    """
    if random.random() < PREFERENCE_WEIGHT:
        candidates = [
            m for m in movies
            if m.id in trending_ids
            or (preferred_category_id and preferred_category_id in movie_categories.get(m.id, []))
        ]
        if candidates:
            return random.choice(candidates), True

    # 20% còn lại (hoặc không tìm được candidate đúng gu) -> random thuần
    return random.choice(movies), False


def _generate_duration_watched(in_preference: bool) -> int:
    ratio_range = HIGH_WATCH_RATIO_RANGE if in_preference else LOW_WATCH_RATIO_RANGE
    ratio = random.uniform(*ratio_range)
    duration = int(ratio * ASSUMED_FULL_DURATION_SECONDS)
    return max(DURATION_WATCHED_MIN, min(duration, DURATION_WATCHED_MAX))


@celery_instance.task(
    bind=True,
    name="tasks.simulate_user_traffic",
    max_retries=2,
    default_retry_delay=60,
    queue="light_queue",
    acks_late=True,
)
def task_simulate_user_traffic(self, days_back: int = 1):
    if days_back < 1:
        days_back = 1

    db = SessionLocal()
    try:
        # Load full model (không chỉ id/name như trước) để lấy quan hệ
        # categories -> cần cho việc gán "gu" và chọn phim đúng Pareto.
        movies = (
            db.query(MovieModel)
            .options(selectinload(MovieModel.categories))
            .filter(MovieModel.is_deleted == False)
            .order_by(func.rand())
            .limit(POOL_SIZE)
            .all()
        )

        movie_ids = [mv.id for mv in movies]
        episode_rows = (
            db.query(EpisodeModel.id, EpisodeModel.id_movie)
            .filter(EpisodeModel.id_movie.in_(movie_ids))
            .all()
        ) if movie_ids else []

        episodes_by_movie: dict[str, list[str]] = {}
        for ep_id, ep_movie_id in episode_rows:
            episodes_by_movie.setdefault(ep_movie_id, []).append(ep_id)

    except Exception as exc:
        logger.exception("[SimTraffic] Lỗi query MySQL: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()

    if not movies:
        logger.warning("[SimTraffic] Không có phim hoạt động — bỏ qua")
        return {"picked": 0, "views_added": 0, "likes_added": 0}

    # ── Setup Pareto + category map — tính 1 LẦN cho cả task run ─────────
    movie_categories: dict[str, list[str]] = {
        mv.id: [c.id for c in mv.categories] for mv in movies
    }
    category_ids = sorted({cid for cids in movie_categories.values() for cid in cids})

    trending_count = max(1, int(len(movies) * TRENDING_RATIO))
    trending_ids = {m.id for m in random.sample(movies, min(trending_count, len(movies)))}

    logger.info(
        "[SimTraffic] Pareto setup: %d/%d phim Trending, %d category khả dụng",
        len(trending_ids), len(movies), len(category_ids),
    )

    now = datetime.now(timezone.utc)

    total_views  = 0
    total_likes  = 0
    total_logged = 0
    daily_breakdown = []

    db_analytics = AnalyticsSessionLocal()
    try:
        for day_offset in range(days_back, 0, -1):
            target_date = now - timedelta(days=day_offset)
            is_weekend  = target_date.weekday() in (5, 6)

            if is_weekend:
                day_view_min, day_view_max = VIEW_MIN, int(VIEW_MAX * WEEKEND_MULTIPLIER)
                day_like_min, day_like_max = LIKE_MIN, int(LIKE_MAX * WEEKEND_MULTIPLIER)
            else:
                day_view_min, day_view_max = VIEW_MIN, VIEW_MAX
                day_like_min, day_like_max = LIKE_MIN, LIKE_MAX

            k_slots = random.randint(PICK_MIN, PICK_MAX)
            # Tổng ngân sách view của ngày (giữ magnitude tương đương bản
            # cũ), nhưng giờ được PHÂN PHỐI theo trọng số gu/trending thay
            # vì dồn hết vào 1 tập con phim cố định.
            total_day_views = sum(
                random.randint(day_view_min, day_view_max) for _ in range(k_slots)
            )
            like_pick = random.sample(movies, min(k_slots, len(movies)))

            es_actions: list = []
            view_log_rows: list = []
            per_movie_view_count: dict[str, int] = {}
            per_movie_like_count: dict[str, int] = {}

            for _ in range(total_day_views):
                user_id = _pick_simulated_user_id()
                preferred_category_id = (
                    None if user_id == "anonymous"
                    else get_preferred_category_id(user_id, category_ids)
                )
                movie, in_preference = _pick_movie_for_user(
                    movies, movie_categories, trending_ids, preferred_category_id
                )

                h = random.randint(0, 23)
                m_ = random.randint(0, 59)
                s = random.randint(0, 59)
                ts = datetime(
                    target_date.year, target_date.month, target_date.day,
                    h, m_, s, tzinfo=timezone.utc,
                )

                es_actions.append({
                    "_index": "movie_interactions_log",
                    "_source": {
                        "movie_id": str(movie.id),
                        "action": "view",
                        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                })

                movie_episodes = episodes_by_movie.get(movie.id)
                view_log_rows.append(MovieViewLogModel(
                    user_id=user_id,
                    movie_id=movie.id,
                    episode_id=random.choice(movie_episodes) if movie_episodes else None,
                    duration_watched=_generate_duration_watched(in_preference),
                    created_at=ts,
                ))

                per_movie_view_count[movie.id] = per_movie_view_count.get(movie.id, 0) + 1

            day_views = total_day_views
            day_likes = 0
            for movie in like_pick:
                n_likes = random.randint(day_like_min, day_like_max)
                per_movie_like_count[movie.id] = per_movie_like_count.get(movie.id, 0) + n_likes
                day_likes += n_likes

                for _ in range(n_likes):
                    h = random.randint(0, 23)
                    m_ = random.randint(0, 59)
                    s = random.randint(0, 59)
                    ts = datetime(
                        target_date.year, target_date.month, target_date.day,
                        h, m_, s, tzinfo=timezone.utc,
                    )
                    es_actions.append({
                        "_index": "movie_interactions_log",
                        "_source": {
                            "movie_id": str(movie.id),
                            "action": "like",
                            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                        }
                    })

            pipe = _redis.pipeline(transaction=False)
            for movie_id, cnt in per_movie_view_count.items():
                pipe.incrby(f"view:{movie_id}", cnt)
            for movie_id, cnt in per_movie_like_count.items():
                pipe.incrby(f"like:{movie_id}", cnt)
            pipe.execute()

            if es_actions:
                success_count, failed = bulk(es_client, es_actions)
                logger.info(
                    "[SimTraffic] Ngày %s (%s): bulk sync %d tài liệu vào ES ✓",
                    target_date.date().isoformat(),
                    "cuối tuần" if is_weekend else "ngày thường",
                    success_count,
                )
                if failed:
                    logger.error(
                        "[SimTraffic] Ngày %s: bulk thất bại %d bản ghi",
                        target_date.date().isoformat(), len(failed),
                    )

            if view_log_rows:
                db_analytics.bulk_save_objects(view_log_rows)
                db_analytics.commit()
                logger.info(
                    "[SimTraffic] Ngày %s: bulk insert %d dòng movie_view_logs ✓",
                    target_date.date().isoformat(), len(view_log_rows),
                )
                total_logged += len(view_log_rows)

            total_views += day_views
            total_likes += day_likes
            daily_breakdown.append({
                "date": target_date.date().isoformat(),
                "is_weekend": is_weekend,
                "views_added": day_views,
                "likes_added": day_likes,
                "view_logs_inserted": len(view_log_rows),
            })

    except Exception as exc:
        db_analytics.rollback()
        logger.exception("[SimTraffic] Lỗi pipeline: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db_analytics.close()

    result = {
        "days_back": days_back,
        "days_processed": len(daily_breakdown),
        "views_added": total_views,
        "likes_added": total_likes,
        "view_logs_inserted": total_logged,
        "trending_movie_ids": list(trending_ids),
        "daily_breakdown": daily_breakdown,
    }
    logger.info("[SimTraffic] Hoàn tất (%d ngày): %s", len(daily_breakdown), result)
    return result