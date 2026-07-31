# src/infrastructure/celery/view_log_task.py
"""
Write-Behind Caching cho lượt xem phim:
Redis List (buffer:movie_views) → Celery Bulk Task → PostgreSQL (raw log) + Elasticsearch.

QUYẾT ĐỊNH KIẾN TRÚC (đã thống nhất): task này KHÔNG đụng tới
movie_daily_statistics. views_count/likes_count/click_count vẫn do
aggregate_task.py tổng hợp mỗi đêm từ ES index movie_interactions_log
như cũ. Task này chỉ SINH DỮ LIỆU NGUỒN (raw log + ES event) — nếu nó
cũng tự cộng views_count, số liệu sẽ bị đếm 2 lần khi aggregate_task.py
quét lại đúng các document mà task này vừa index.
"""
import json
import logging
import os
from datetime import datetime, timezone

from elasticsearch.helpers import bulk
from redis import Redis as SyncRedis

from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.database.analytics_session import AnalyticsSessionLocal
from src.infrastructure.database.models.analytics.movie_view_log import MovieViewLogModel
from src.infrastructure.elasticsearch.es_client import es_client

logger = logging.getLogger(__name__)

VIEW_BUFFER_KEY = "buffer:movie_views"
INTERACTION_INDEX = "movie_interactions_log"
FLUSH_BATCH_SIZE = 500


def _parse_timestamp(raw_ts: str | None) -> datetime:
    if not raw_ts:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw_ts)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


@celery_instance.task(
    bind=True,
    name="tasks.flush_view_logs_buffer",
    max_retries=2,
    default_retry_delay=30,
    queue="light_queue",
    acks_late=True,
)
def flush_view_logs_buffer(self):
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/1")
    r = SyncRedis.from_url(redis_url, decode_responses=True)

    # ── Bước 1: Rút tối đa 500 item khỏi buffer ─────────────────────────────
    try:
        raw_items = r.lpop(VIEW_BUFFER_KEY, FLUSH_BATCH_SIZE)
    except Exception as exc:
        logger.exception("[FlushViewLogs] Không đọc được Redis buffer: %s", exc)
        r.close()
        raise self.retry(exc=exc)

    if not raw_items:
        r.close()
        return {"status": "Success", "msg": "Buffer rỗng, không có gì để flush"}

    # ── Bước 2: Parse JSON, bỏ qua item lỗi format ──────────────────────────
    events = []
    for raw in raw_items:
        try:
            events.append(json.loads(raw))
        except (TypeError, ValueError):
            logger.warning("[FlushViewLogs] Bỏ qua item JSON lỗi: %s", raw)

    if not events:
        r.close()
        return {"status": "Success", "msg": "Không parse được item nào hợp lệ"}

    db = AnalyticsSessionLocal()
    try:
        # ── Bước 3: Bulk insert raw log vào PostgreSQL ──────────────────────
        log_rows = [
            MovieViewLogModel(
                user_id=ev.get("user_id"),
                movie_id=ev["movie_id"],
                episode_id=ev.get("episode_id"),
                duration_watched=ev.get("duration_watched", 0),
                created_at=_parse_timestamp(ev.get("timestamp")),
            )
            for ev in events
        ]
        db.bulk_save_objects(log_rows)
        db.commit()
        logger.info("[FlushViewLogs] Đã bulk insert %d raw log vào PostgreSQL", len(log_rows))

        # ── Bước 4: Bulk index sang Elasticsearch ───────────────────────────
        es_actions = [
            {
                "_index": INTERACTION_INDEX,
                "_source": {
                    "action": "view",
                    "user_id": ev.get("user_id"),
                    "movie_id": ev["movie_id"],
                    "episode_id": ev.get("episode_id"),
                    "duration_watched": ev.get("duration_watched", 0),
                    "@timestamp": ev.get("timestamp") or _parse_timestamp(None).isoformat(),
                },
            }
            for ev in events
        ]
        success_count, es_errors = bulk(es_client, es_actions, raise_on_error=False)
        if es_errors:
            logger.warning("[FlushViewLogs] %d document lỗi khi index ES (5 đầu): %s",
                            len(es_errors), es_errors[:5])
        logger.info("[FlushViewLogs] Đã index %d/%d document vào ES", success_count, len(es_actions))

        return {
            "status": "Success",
            "flushed": len(events),
            "db_inserted": len(log_rows),
            "es_indexed": success_count,
        }

    except Exception as exc:
        db.rollback()
        logger.exception(
            "[FlushViewLogs] Lỗi khi flush buffer, đẩy trả %d item lại Redis: %s",
            len(raw_items), exc,
        )
        # Đẩy trả lại RAW string (chưa parse) vào ĐẦU list để lần sau xử lý
        # lại đúng những item này trước — lpush theo thứ tự ngược để giữ
        # nguyên thứ tự ban đầu sau khi đẩy trả.
        r.lpush(VIEW_BUFFER_KEY, *reversed(raw_items))
        raise self.retry(exc=exc)

    finally:
        db.close()
        r.close()