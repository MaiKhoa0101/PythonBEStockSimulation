# src/infrastructure/celery/aggregate_task.py
"""
Task gom nhóm dữ liệu tương tác từ Elasticsearch → PostgreSQL.

Flow (mặc định, days_back=1):
    [Celery Beat, chạy 01:00 sáng mỗi ngày]
        ↓
    Query ES: lấy toàn bộ sự kiện của NGÀY HÔM QUA (composite pagination)
        ↓
    ES Aggregation: đếm view + like theo từng movie_id × giờ
        ↓
    Upsert vào PostgreSQL (bảng movie_daily_statistics)
        ↓
    Ghi log SUCCESS / FAILURE vào CeleryTaskLog (qua signals.py)

Backfill lịch sử (days_back)
─────────────────────────────────────────────────────────
    Đồng bộ với simulate_traffic_task: khi gọi task này với days_back > 1
    (vd: 120), nó lặp cuốn chiếu từ "days_back ngày trước" cho tới "hôm
    qua". MỖI ngày được query ES, parse và upsert Postgres RIÊNG BIỆT
    (không gộp chung 1 query lớn) — để log rõ ràng theo từng ngày.

    Dùng khi cần nạp đầy movie_daily_statistics sau khi đã bơm dữ liệu
    giả bằng simulate_traffic_task(days_back=N):
        task_simulate_user_traffic.delay(days_back=120)
        # đợi task trên chạy xong rồi mới gọi:
        task_aggregate_es_to_postgres.delay(days_back=120)

Composite Aggregation + Pagination (after_key)
─────────────────────────────────────────────────────────
    THAY ĐỔI QUAN TRỌNG: trước đây dùng "terms" (movie_id) lồng
    "date_histogram" (giờ) — ES phải build TOÀN BỘ cây bucket
    (số_phim × số_giờ) trong RAM cùng lúc để trả về 1 lần, dễ vượt giới
    hạn `search.max_buckets` (mặc định 65,536) khi dữ liệu lớn.

    Giờ dùng "composite" aggregation: gộp (movie_id, giờ) thành 1 khóa
    ghép phẳng, mỗi lần gọi ES chỉ trả về tối đa COMPOSITE_PAGE_SIZE
    bucket (mặc định 1000) — an toàn tuyệt đối dưới giới hạn dù dữ liệu
    lớn tới đâu. Lặp gọi ES nhiều lần, mỗi lần truyền "after_key" của
    lần trước để lấy tiếp trang kế, cho tới khi ES không còn trả
    after_key nữa (đã lấy hết dữ liệu của ngày đó).
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

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

# Độ phân giải bucket khi gom nhóm từ ES → mỗi dòng Postgres = 1 bucket.
# Đổi thành "minute" nếu cần chi tiết tới từng phút (⚠️ tăng số bucket cần
# lặp trang đáng kể). Các giá trị hợp lệ khác của ES:
# "minute", "hour", "day", "week", "month".
AGG_INTERVAL = "hour"

# Số bucket tối đa mỗi lần gọi ES (1 "trang" composite aggregation).
# Luôn nằm rất xa dưới giới hạn search.max_buckets (65,536 mặc định) —
# không cần chỉnh giá trị này trừ khi có lý do đặc biệt.
COMPOSITE_PAGE_SIZE = 1000


def _get_day_range(days_before: int = 1) -> tuple[str, str, date]:
    """
    Trả về (start, end, date) cho ngày cách "hôm nay" đúng `days_before`
    ngày, dạng ISO-8601 UTC.

    Ví dụ gọi lúc 2026-07-06 01:00 với days_before=1 (mặc định — hôm qua):
        start = '2026-07-05T00:00:00'
        end   = '2026-07-05T23:59:59'
        date  = 2026-07-05

    Với days_before=120 → ngày cách đây 120 ngày, dùng để backfill.
    """
    today  = datetime.now(timezone.utc).date()
    target = today - timedelta(days=days_before)
    start  = datetime(target.year, target.month, target.day, 0,  0,  0,  tzinfo=timezone.utc)
    end    = datetime(target.year, target.month, target.day, 23, 59, 59, tzinfo=timezone.utc)
    return start.strftime("%Y-%m-%dT%H:%M:%S"), end.strftime("%Y-%m-%dT%H:%M:%S"), target


def _build_composite_query(
    start: str,
    end: str,
    interval: str = AGG_INTERVAL,
    after_key: dict | None = None,
) -> dict:
    """
    Xây câu truy vấn Elasticsearch Composite Aggregation — thay thế cho
    terms + date_histogram lồng nhau.

    ── Giải thích cú pháp ──────────────────────────────────────────────────

    "composite.sources"
        → Danh sách field ghép thành 1 khóa duy nhất, đóng vai trò như
          GROUP BY movie_id, giờ nhưng KHÔNG lồng cây — phẳng ra 1 tầng.

    "composite.size"
        → Giới hạn CỨNG số bucket trả về MỖI LẦN GỌI (1 trang). ES không
          bao giờ build nhiều hơn con số này trong RAM cùng lúc.

    "composite.after"
        → Con trỏ phân trang, lấy từ "after_key" của response lần gọi
          trước. Bỏ qua ở lần gọi đầu tiên (trang đầu).

    Kết quả trả về dạng:
    {
        "aggregations": {
            "movie_hour_buckets": {
                "after_key": {"movie_id": "...", "time_bucket": 1720137600000},
                "buckets": [
                    {
                        "key": {"movie_id": "movie-abc", "time_bucket": 1720137600000},
                        "doc_count": 15,
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
        }
    }

    LƯU Ý: "time_bucket" ở đây là EPOCH MILLISECONDS (số), KHÁC với
    date_histogram thường (trả "key_as_string" dạng chuỗi ISO) — cần
    parse bằng datetime.fromtimestamp(ms / 1000, tz=timezone.utc), không
    dùng strptime.
    ──────────────────────────────────────────────────────────────────────
    """
    composite_agg = {
        "size": COMPOSITE_PAGE_SIZE,
        "sources": [
            {"movie_id": {"terms": {"field": "movie_id.keyword"}}},
            {
                "time_bucket": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": interval,
                        "time_zone": "UTC",
                    }
                }
            },
        ],
    }
    if after_key:
        composite_agg["after"] = after_key

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
            "movie_hour_buckets": {
                "composite": composite_agg,
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


def _fetch_all_composite_buckets(start: str, end: str, interval: str = AGG_INTERVAL) -> list[dict]:
    """
    Lặp gọi ES theo từng trang (composite + after_key) cho tới khi lấy
    hết toàn bộ bucket của khoảng thời gian [start, end]. Mỗi lần gọi
    ES chỉ trả về tối đa COMPOSITE_PAGE_SIZE bucket — không bao giờ chạm
    giới hạn search.max_buckets dù tổng dữ liệu có bao nhiêu bucket.

    Trả về danh sách dòng phẳng, mỗi phần tử = 1 bucket (movie × giờ):
        [
            {"movie_id": "movie-abc", "date": datetime(...), "views_count": 12, "likes_count": 3},
            ...
        ]
    """
    all_rows: list[dict] = []
    after_key: dict | None = None
    page_number = 0

    while True:
        page_number += 1
        query = _build_composite_query(start, end, interval, after_key)
        response = es_client.search(index=INTERACTION_INDEX, body=query)

        agg_result = response.get("aggregations", {}).get("movie_hour_buckets", {})
        buckets = agg_result.get("buckets", [])

        if not buckets:
            break  # hết dữ liệu (hoặc trang đầu đã rỗng)

        for bucket in buckets:
            key = bucket["key"]  # {"movie_id": "...", "time_bucket": <epoch_millis>}

            counts = {"view": 0, "like": 0}
            for action_bucket in bucket.get("by_action", {}).get("buckets", []):
                action = action_bucket["key"]
                if action in counts:
                    counts[action] = action_bucket["doc_count"]

            all_rows.append({
                "movie_id":    key["movie_id"],
                "date":        datetime.fromtimestamp(key["time_bucket"] / 1000, tz=timezone.utc),
                "views_count": counts["view"],
                "likes_count": counts["like"],
            })

        after_key = agg_result.get("after_key")
        logger.debug(
            "[Aggregate] Trang %d: nhận %d bucket, after_key=%s",
            page_number, len(buckets), after_key,
        )

        if not after_key:
            break  # ES không còn trang tiếp theo

    logger.info(
        "[Aggregate] Composite pagination hoàn tất: %d trang, tổng %d bucket",
        page_number, len(all_rows),
    )
    return all_rows


def _upsert_to_postgres(rows: list[dict]) -> int:
    """
    Ghi toàn bộ kết quả vào PostgreSQL bằng INSERT ... ON CONFLICT DO UPDATE.

    `rows` đã ở dạng phẳng (mỗi phần tử = 1 bucket thời gian của 1 phim,
    xem _fetch_all_composite_buckets), nên chỉ cần thêm "id" trước khi insert.

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
def task_aggregate_es_to_postgres(self, days_back: int = 1):
    """
    Tổng hợp dữ liệu tương tác từ Elasticsearch → PostgreSQL.
    Chạy định kỳ lúc 01:00 sáng mỗi ngày để xử lý dữ liệu của ngày hôm qua.

    Tham số:
        days_back (int): Số ngày cần tổng hợp, tính lùi từ hôm qua.
            - days_back = 1 (mặc định): chỉ tổng hợp NGÀY HÔM QUA
              (giữ nguyên hành vi cũ, dùng cho lịch chạy 01:00 sáng).
            - days_back > 1: lặp cuốn chiếu từ "days_back ngày trước"
              cho tới "hôm qua", query + parse + upsert RIÊNG BIỆT cho
              từng ngày. Dùng để backfill Postgres khớp với dữ liệu ES
              đã được simulate_traffic_task(days_back=N) bơm vào trước đó.
    """
    if days_back < 1:
        days_back = 1

    if not es_client.indices.exists(index=INTERACTION_INDEX):
        logger.warning(f"[Aggregate] Index {INTERACTION_INDEX} chưa tồn tại trên ES. Mặc định hôm nay không có tương tác nào.")
        return {"status": "Success", "msg": "Index empty, skipped aggregation"}

    logger.info(
        "[Aggregate] Bắt đầu tổng hợp %d ngày dữ liệu, bucket=%s (composite pagination, page_size=%d)",
        days_back, AGG_INTERVAL, COMPOSITE_PAGE_SIZE,
    )

    daily_breakdown: list[dict] = []
    total_upserted  = 0

    # 💡 Lặp cuốn chiếu từ "days_back ngày trước" cho tới "hôm qua".
    # days_back=1 → chỉ 1 vòng lặp với offset=1 (hôm qua), y hệt logic cũ.
    for day_offset in range(days_back, 0, -1):
        start_str, end_str, target_date = _get_day_range(day_offset)
        logger.info(
            "[Aggregate] Ngày %s (%s → %s)",
            target_date, start_str, end_str,
        )

        # ── Bước 1+2: Query + parse ES qua composite pagination (cho ngày này) ──
        try:
            rows = _fetch_all_composite_buckets(start_str, end_str, AGG_INTERVAL)
        except Exception as exc:
            logger.exception("[Aggregate] Ngày %s: composite query thất bại: %s", target_date, exc)
            raise self.retry(exc=exc)

        if not rows:
            logger.warning(
                "[Aggregate] Ngày %s không có tương tác nào trong ES — bỏ qua upsert",
                target_date,
            )
            daily_breakdown.append({"date": str(target_date), "buckets": 0, "upserted": 0})
            continue

        # ── Bước 3: Upsert vào PostgreSQL (cho ngày này) ────────────────────
        try:
            upserted = _upsert_to_postgres(rows)
        except Exception as exc:
            logger.exception("[Aggregate] Ngày %s: upsert PostgreSQL thất bại: %s", target_date, exc)
            raise self.retry(exc=exc)

        total_upserted += upserted
        daily_breakdown.append({"date": str(target_date), "buckets": len(rows), "upserted": upserted})

    result = {
        "days_back":       days_back,
        "days_processed":  len(daily_breakdown),
        "total_upserted":  total_upserted,
        "daily_breakdown": daily_breakdown,
    }
    logger.info("[Aggregate] Hoàn thành: %s", result)
    return result