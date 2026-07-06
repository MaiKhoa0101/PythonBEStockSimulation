# src/infrastructure/celery/aggregate_task.py
"""
Task gom nhóm dữ liệu tương tác từ Elasticsearch → PostgreSQL.

Flow:
    [Celery Beat, chạy 01:00 sáng mỗi ngày]
        ↓
    Query ES: lấy toàn bộ sự kiện của NGÀY HÔM QUA
        ↓
    ES Aggregation: đếm view + like theo từng movie_id
        ↓
    Upsert vào PostgreSQL (bảng movie_daily_statistics)
        ↓
    Ghi log SUCCESS / FAILURE vào CeleryTaskLog (qua signals.py)
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Dict

from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.database.analytics_session import AnalyticsSessionLocal
from src.infrastructure.database.models.analytics.movie_daily_statistic import (
    MovieDailyStatistic,
)
from src.infrastructure.elasticsearch.es_client import es_client

logger = logging.getLogger(__name__)

# ── Hằng số 
INTERACTION_INDEX = "movie_interactions_log"
MAX_MOVIES_PER_DAY = 10_000 

def _get_yesterday_range() -> tuple[str, str]:
    """
    Trả về (start, end) của ngày hôm qua dạng ISO-8601 UTC.
    Ví dụ gọi lúc 2026-07-06 01:00:
        start = '2026-07-05T00:00:00'
        end   = '2026-07-05T23:59:59'
    """
    today     = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    start     = datetime(yesterday.year, yesterday.month, yesterday.day, 0,  0,  0,  tzinfo=timezone.utc)
    end       = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=timezone.utc)
    return start.strftime("%Y-%m-%dT%H:%M:%S"), end.strftime("%Y-%m-%dT%H:%M:%S"), yesterday


def _build_es_query(start: str, end: str) -> dict:
    """
    Xây câu truy vấn Elasticsearch Aggregation.

    ── Giải thích cú pháp ──────────────────────────────────────────────────────

    "size": 0
        → Không trả về document gốc, chỉ cần kết quả aggregation.
          Tiết kiệm băng thông đáng kể khi có hàng triệu bản ghi.

    "query.bool.filter"
        → Lọc document trước khi aggregate.
          Dùng filter thay vì must vì không cần tính relevance score
          → ES bỏ qua tính điểm, nhanh hơn và kết quả có thể cache.

    "range.timestamp"
        gte (greater than or equal) = từ 00:00:00
        lte (less than or equal)    = đến 23:59:59
        format = strict_date_hour_minute_second → ES validate format đầu vào

    "aggs.by_movie" (terms aggregation — cấp 1)
        → Gom nhóm theo movie_id, giống GROUP BY movie_id trong SQL.
        "size": 10000 → lấy tối đa 10k movie_id có nhiều lượt nhất.
        Nếu có > 10k phim/ngày, tăng size lên.

    "aggs.by_action" (terms aggregation — cấp 2, nested bên trong by_movie)
        → Trong mỗi movie_id, tiếp tục gom nhóm theo action ("view"/"like").
        "size": 2 → chỉ có đúng 2 giá trị nên để 2 là đủ.

    Kết quả trả về dạng:
    {
        "aggregations": {
            "by_movie": {
                "buckets": [
                    {
                        "key": "movie-abc-123",       ← movie_id
                        "doc_count": 150,             ← tổng sự kiện
                        "by_action": {
                            "buckets": [
                                {"key": "view", "doc_count": 120},
                                {"key": "like", "doc_count": 30}
                            ]
                        }
                    },
                    ...
                ]
            }
        }
    }
    ────────────────────────────────────────────────────────────────────────────
    """
    return {
        "size": 0,
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "timestamp": {
                                "gte":    start,
                                "lte":    end,
                                "format": "strict_date_hour_minute_second",
                            }
                        }
                    }
                ]
            }
        },
        "aggs": {
            "by_movie": {
                "terms": {
                    "field": "movie_id",
                    "size":  MAX_MOVIES_PER_DAY,
                },
                "aggs": {
                    "by_action": {
                        "terms": {
                            "field": "action",
                            "size":  2,
                        }
                    }
                },
            }
        },
    }


def _parse_aggregation(response: dict) -> Dict[str, dict]:
    """
    Chuyển kết quả ES aggregation thành dict Python thuần.

    Trả về:
        {
            "movie-abc-123": {"view": 120, "like": 30},
            "movie-xyz-456": {"view": 70,  "like": 10},
        }
    """
    result: Dict[str, dict] = {}
    buckets = response.get("aggregations", {}).get("by_movie", {}).get("buckets", [])

    for movie_bucket in buckets:
        movie_id = movie_bucket["key"]
        counts   = {"view": 0, "like": 0}

        for action_bucket in movie_bucket.get("by_action", {}).get("buckets", []):
            action = action_bucket["key"]
            if action in counts:
                counts[action] = action_bucket["doc_count"]

        result[movie_id] = counts

    return result


def _upsert_to_postgres(stats: Dict[str, dict], target_date: date) -> int:
    """
    Ghi toàn bộ kết quả vào PostgreSQL bằng INSERT ... ON CONFLICT DO UPDATE.

    Dùng PostgreSQL native upsert thay vì query-then-update vì:
      1. Atomic — không có race condition nếu task chạy song song.
      2. Nhanh hơn — 1 round-trip thay vì 2 (SELECT + UPDATE).
      3. Tận dụng UNIQUE CONSTRAINT (movie_id, date) đã định nghĩa sẵn.

    Trả về số bản ghi đã upsert.
    """
    if not stats:
        logger.warning("[Aggregate] Không có dữ liệu để upsert — stats rỗng")
        return 0

    rows = [
        {
            "id":          str(uuid.uuid4()),
            "movie_id":    movie_id,
            "date":        target_date,
            "views_count": counts["view"],
            "likes_count": counts["like"],
            "click_count": 0,   # click_count không có trong ES log — giữ nguyên nếu đã có
        }
        for movie_id, counts in stats.items()
    ]

    db = AnalyticsSessionLocal()
    try:
        # pg_insert: INSERT INTO movie_daily_statistics (...)
        # on_conflict_do_update: ON CONFLICT (movie_id, date) DO UPDATE SET ...
        #   → Nếu (movie_id, date) đã tồn tại → cập nhật views/likes
        #   → Nếu chưa có → insert mới
        #   → click_count KHÔNG bị overwrite (giữ giá trị đang có trong DB)
        stmt = pg_insert(MovieDailyStatistic).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_movie_date",
            set_={
                "views_count": stmt.excluded.views_count,
                "likes_count": stmt.excluded.likes_count,
                # click_count cố ý không đưa vào — không overwrite dữ liệu khác nguồn
            },
        )
        db.execute(stmt)
        db.commit()

        logger.info("[Aggregate] Upsert %d bản ghi vào PostgreSQL ✓", len(rows))
        return len(rows)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Celery Task ───────────────────────────────────────────────────────────────

@celery_instance.task(
    bind=True,
    name="tasks.aggregate_es_to_postgres",
    max_retries=2,
    default_retry_delay=300,   # Retry sau 5 phút nếu ES/PG tạm thời lỗi
    queue="light_queue",
    acks_late=True,
)
def task_aggregate_es_to_postgres(self):
    """
    Tổng hợp dữ liệu tương tác từ Elasticsearch → PostgreSQL.
    Chạy định kỳ lúc 01:00 sáng mỗi ngày để xử lý dữ liệu của ngày hôm qua.
    """
    start_str, end_str, yesterday = _get_yesterday_range()
    logger.info(
        "[Aggregate] Bắt đầu tổng hợp dữ liệu ngày %s (%s → %s)",
        yesterday, start_str, end_str,
    )

    # ── Bước 1: Query Elasticsearch ──────────────────────────────────────────
    try:
        query    = _build_es_query(start_str, end_str)
        response = es_client.search(index=INTERACTION_INDEX, body=query)
        logger.info(
            "[Aggregate] ES query OK — took %dms, tổng sự kiện: %d",
            response.get("took", 0),
            response.get("hits", {}).get("total", {}).get("value", 0),
        )
    except Exception as exc:
        logger.exception("[Aggregate] ES query thất bại: %s", exc)
        raise self.retry(exc=exc)

    # ── Bước 2: Parse kết quả aggregation ────────────────────────────────────
    try:
        stats = _parse_aggregation(response)
        logger.info("[Aggregate] Parse xong %d movie_id có tương tác", len(stats))
    except Exception as exc:
        logger.exception("[Aggregate] Parse aggregation thất bại: %s", exc)
        raise self.retry(exc=exc)

    if not stats:
        logger.warning(
            "[Aggregate] Ngày %s không có tương tác nào trong ES — bỏ qua upsert",
            yesterday,
        )
        return {"date": str(yesterday), "upserted": 0}

    # ── Bước 3: Upsert vào PostgreSQL ────────────────────────────────────────
    try:
        upserted = _upsert_to_postgres(stats, yesterday)
    except Exception as exc:
        logger.exception("[Aggregate] Upsert PostgreSQL thất bại: %s", exc)
        raise self.retry(exc=exc)

    result = {"date": str(yesterday), "upserted": upserted}
    logger.info("[Aggregate] Hoàn thành: %s", result)
    return result