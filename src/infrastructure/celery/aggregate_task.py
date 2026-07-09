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
from datetime import datetime, timedelta, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.database.analytics_session import (
    AnalyticsSessionLocal,
    create_analytics_tables,
)
from src.infrastructure.database.models.analytics.movie_daily_statistic import (
    MovieDailyStatistic,
)

from src.infrastructure.elasticsearch.es_client import es_client
create_analytics_tables()

logger = logging.getLogger(__name__)

# ── Hằng số
INTERACTION_INDEX = "movie_interactions_log"
MAX_MOVIES_PER_DAY = 10_000

# Độ phân giải bucket khi gom nhóm từ ES → mỗi dòng Postgres = 1 bucket.
# Đổi thành "minute" nếu cần chi tiết tới từng phút (⚠️ tăng số dòng đáng kể,
# tối đa ~1440 dòng/phim/ngày thay vì 24). Các giá trị hợp lệ khác của ES:
# "minute", "hour", "day", "week", "month".
AGG_INTERVAL = "hour"

# Định dạng key_as_string mà ES trả về khi "format" ở dưới là
# strict_date_hour_minute_second — dùng để parse ngược lại thành datetime.
_ES_BUCKET_FORMAT = "%Y-%m-%dT%H:%M:%S"

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


def _build_es_query(start: str, end: str, interval: str = AGG_INTERVAL) -> dict:
    """
    Xây câu truy vấn Elasticsearch Aggregation.

    ── Giải thích cú pháp ──────────────────────────────────────────────────────

    "size": 0
        → Không trả về document gốc, chỉ cần kết quả aggregation.

    "query.bool.filter"
        → Lọc document trước khi aggregate (dùng filter thay vì must vì
          không cần tính relevance score → nhanh hơn, cache được).

    "aggs.by_movie" (terms — cấp 1)
        → Gom theo movie_id, giống GROUP BY movie_id.

    "aggs.by_movie.aggs.by_time" (date_histogram — cấp 2, MỚI)
        → Trong mỗi phim, tiếp tục chia nhỏ theo từng bucket thời gian
          (mặc định 1 giờ, xem AGG_INTERVAL). Đây là phần cho phép sau
          này gom nhóm lại theo phút/giờ/ngày/tuần/tháng ở Postgres —
          không thể gom mịn hơn độ phân giải này.

    "aggs.by_movie.aggs.by_time.aggs.by_action" (terms — cấp 3)
        → Trong mỗi bucket thời gian, đếm view/like.

    Kết quả trả về dạng:
    {
        "aggregations": {
            "by_movie": {
                "buckets": [
                    {
                        "key": "movie-abc-123",
                        "by_time": {
                            "buckets": [
                                {
                                    "key_as_string": "2026-07-05T00:00:00",
                                    "by_action": {
                                        "buckets": [
                                            {"key": "view", "doc_count": 12},
                                            {"key": "like", "doc_count": 3}
                                        ]
                                    }
                                },
                                ...
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
                    "field": "movie_id.keyword",
                    "size":  MAX_MOVIES_PER_DAY,
                },
                "aggs": {
                    "by_time": {
                        "date_histogram": {
                            "field":            "timestamp",
                            "calendar_interval": interval,
                            "time_zone":        "UTC",
                            "format":           "strict_date_hour_minute_second",
                            "min_doc_count":    1,
                        },
                        "aggs": {
                            "by_action": {
                                "terms": {
                                    "field": "action.keyword",
                                    "size":  2,
                                }
                            }
                        },
                    }
                },
            }
        },
    }


def _parse_aggregation(response: dict) -> list[dict]:
    """
    Chuyển kết quả ES aggregation thành danh sách dòng phẳng, mỗi phần tử
    là 1 bucket thời gian của 1 phim — khớp trực tiếp với 1 dòng Postgres.

    Trả về:
        [
            {"movie_id": "movie-abc-123", "date": datetime(...), "views_count": 12, "likes_count": 3},
            ...
        ]
    """
    rows: list[dict] = []
    buckets = response.get("aggregations", {}).get("by_movie", {}).get("buckets", [])

    for movie_bucket in buckets:
        movie_id = movie_bucket["key"]

        for time_bucket in movie_bucket.get("by_time", {}).get("buckets", []):
            bucket_start = datetime.strptime(
                time_bucket["key_as_string"], _ES_BUCKET_FORMAT
            ).replace(tzinfo=timezone.utc)

            counts = {"view": 0, "like": 0}
            for action_bucket in time_bucket.get("by_action", {}).get("buckets", []):
                action = action_bucket["key"]
                if action in counts:
                    counts[action] = action_bucket["doc_count"]

            rows.append({
                "movie_id":    movie_id,
                "date":        bucket_start,
                "views_count": counts["view"],
                "likes_count": counts["like"],
            })

    return rows


def _upsert_to_postgres(rows: list[dict]) -> int:
    """
    Ghi toàn bộ kết quả vào PostgreSQL bằng INSERT ... ON CONFLICT DO UPDATE.

    `rows` đã ở dạng phẳng (mỗi phần tử = 1 bucket thời gian của 1 phim,
    xem _parse_aggregation), nên chỉ cần thêm "id" trước khi insert.

    Dùng PostgreSQL native upsert thay vì query-then-update vì:
      1. Atomic — không có race condition nếu task chạy song song.
      2. Nhanh hơn — 1 round-trip thay vì 2 (SELECT + UPDATE).
      3. Tận dụng UNIQUE CONSTRAINT (movie_id, date) đã định nghĩa sẵn.

    Trả về số bản ghi đã upsert.
    """
    if not rows:
        logger.warning("[Aggregate] Không có dữ liệu để upsert — rows rỗng")
        return 0

    values = [
        {
            "id":          str(uuid.uuid4()),
            "movie_id":    r["movie_id"],
            "date":        r["date"],
            "views_count": r["views_count"],
            "likes_count": r["likes_count"],
            "click_count": 0,   # click_count không có trong ES log — giữ nguyên nếu đã có
        }
        for r in rows
    ]

    db = AnalyticsSessionLocal()
    try:
        stmt = pg_insert(MovieDailyStatistic).values(values)
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

        logger.info("[Aggregate] Upsert %d bucket(s) vào PostgreSQL ✓", len(values))
        return len(values)

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
    default_retry_delay=300,
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
        "[Aggregate] Bắt đầu tổng hợp dữ liệu ngày %s (%s → %s), bucket=%s",
        yesterday, start_str, end_str, AGG_INTERVAL,
    )
    if not es_client.indices.exists(index=INTERACTION_INDEX):
            logger.warning(f"[Aggregate] Index {INTERACTION_INDEX} chưa tồn tại trên ES. Mặc định hôm nay không có tương tác nào.")
            return {"status": "Success", "msg": "Index empty, skipped aggregation"}
    
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

    # ── Bước 2: Parse kết quả aggregation ─────────────────────────────────────
    try:
        rows = _parse_aggregation(response)
        logger.info("[Aggregate] Parse xong %d bucket (movie × thời gian)", len(rows))
    except Exception as exc:
        logger.exception("[Aggregate] Parse aggregation thất bại: %s", exc)
        raise self.retry(exc=exc)

    if not rows:
        logger.warning(
            "[Aggregate] Ngày %s không có tương tác nào trong ES — bỏ qua upsert",
            yesterday,
        )
        return {"date": str(yesterday), "buckets": 0, "upserted": 0}

    # ── Bước 3: Upsert vào PostgreSQL ────────────────────────────────────────
    try:
        upserted = _upsert_to_postgres(rows)
    except Exception as exc:
        logger.exception("[Aggregate] Upsert PostgreSQL thất bại: %s", exc)
        raise self.retry(exc=exc)

    result = {"date": str(yesterday), "buckets": len(rows), "upserted": upserted}
    logger.info("[Aggregate] Hoàn thành: %s", result)
    return result