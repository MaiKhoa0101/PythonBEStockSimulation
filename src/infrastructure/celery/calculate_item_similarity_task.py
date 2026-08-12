import json
import logging
import os

import pandas as pd
import redis
from sklearn.metrics.pairwise import cosine_similarity

from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.database.analytics_session import AnalyticsSessionLocal
from src.infrastructure.database.models.analytics.movie_view_log import MovieViewLogModel

logger = logging.getLogger(__name__)

_redis = redis.from_url(
    os.getenv("REDIS_URL_CACHE"),
    decode_responses=True,
)

TOP_N_SIMILAR = 5
HABIT_CACHE_TTL = 7 * 24 * 3600  # 7 ngày

# Không áp threshold theo yêu cầu hiện tại. Để sẵn công tắc (0 = tắt) cho
# tương lai khi có dữ liệu người dùng thật (vd lọc log <10s do bấm nhầm).
MIN_DURATION_WATCHED_SECONDS = 0


@celery_instance.task(
    bind=True,
    name="tasks.calculate_item_similarity",
    max_retries=2,
    default_retry_delay=300,
    queue="heavy_queue",
    acks_late=True,
)
def calculate_item_similarity_task(self):
    db = AnalyticsSessionLocal()
    try:
        query = db.query(
            MovieViewLogModel.user_id,
            MovieViewLogModel.movie_id,
            MovieViewLogModel.duration_watched,
        ).filter(
            MovieViewLogModel.user_id != "anonymous",
            MovieViewLogModel.user_id.isnot(None),
        )
        if MIN_DURATION_WATCHED_SECONDS > 0:
            query = query.filter(
                MovieViewLogModel.duration_watched >= MIN_DURATION_WATCHED_SECONDS
            )
        rows = query.all()
    except Exception as exc:
        logger.exception("[ItemSimilarity] Lỗi query movie_view_logs: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()

    if not rows:
        logger.warning("[ItemSimilarity] Không có dữ liệu view log hợp lệ — bỏ qua")
        return {"movies_processed": 0}

    df = pd.DataFrame(rows, columns=["user_id", "movie_id", "duration_watched"])

    # 1 user có thể xem cùng 1 phim nhiều lượt (nhiều tập/nhiều lần) ->
    # cộng dồn duration_watched, thể hiện mức độ "gắn bó" cao hơn xem 1 lần.
    matrix = df.pivot_table(
        index="user_id",
        columns="movie_id",
        values="duration_watched",
        aggfunc="sum",
        fill_value=0,
    )

    if matrix.shape[1] < 2:
        logger.warning("[ItemSimilarity] Không đủ số phim để tính similarity (cần >= 2)")
        return {"movies_processed": 0}

    # cosine_similarity tính theo HÀNG -> transpose để mỗi hàng đại diện 1 phim
    sim_matrix = cosine_similarity(matrix.T.values)
    movie_ids = matrix.columns.tolist()

    saved_count = 0
    pipe = _redis.pipeline(transaction=False)

    for i, movie_id in enumerate(movie_ids):
        scores = [(idx, score) for idx, score in enumerate(sim_matrix[i]) if idx != i]
        scores.sort(key=lambda x: x[1], reverse=True)
        top_similar_ids = [
            movie_ids[idx] for idx, score in scores[:TOP_N_SIMILAR] if score > 0
        ]

        if top_similar_ids:
            pipe.set(f"movie:{movie_id}:habit", json.dumps(top_similar_ids), ex=HABIT_CACHE_TTL)
            saved_count += 1

    pipe.execute()

    logger.info(
        "[ItemSimilarity] Hoàn tất: %d phim có dữ liệu, %d phim được lưu vào Redis",
        len(movie_ids), saved_count,
    )
    return {"movies_processed": len(movie_ids), "movies_saved": saved_count}