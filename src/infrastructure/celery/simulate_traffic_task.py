# src/infrastructure/celery/simulate_traffic_task.py
"""
Task giả lập traffic người dùng để kiểm thử Dashboard Analytics.

Tại sao bơm vào Redis thay vì ghi thẳng MySQL/PostgreSQL?
─────────────────────────────────────────────────────────
  MySQL INCRBY trực tiếp       Redis INCRBY
  ──────────────────────────   ──────────────────────────────
  SELECT + UPDATE + COMMIT     INCRBY — 1 lệnh, ~0.1ms
  ~5–20ms / ghi                Lock-free, không blocking
  Row lock khi nhiều task      Atomic tự nhiên
  Không chịu được traffic spike Hấp thụ spike tốt

  → Pattern Write-Behind Buffer:
    Redis gom counter trong RAM.
    Task sync_view_count (đã có, chạy mỗi 5 phút)
    định kỳ flush toàn bộ counter xuống MySQL.
    Dashboard đọc từ MySQL sau flush.

Backfill lịch sử (days_back)
─────────────────────────────────────────────────────────
  Mặc định (days_back=1) task chạy đúng như chu kỳ 5 phút cũ: chỉ sinh
  dữ liệu cho NGÀY HÔM QUA.

  Khi cần nạp đầy dữ liệu lịch sử để Admin Dashboard có đủ số liệu vẽ
  biểu đồ theo tuần/tháng, gọi task với days_back > 1 (vd: 14, 30).
  Task sẽ lặp cuốn chiếu từ "N ngày trước" cho tới "hôm qua", mỗi vòng
  lặp là một ngày độc lập: tự bốc phim, tự sinh view/like, tự ghi
  Redis + Elasticsearch riêng cho ngày đó — để dữ liệu phân rã đều
  theo trục thời gian thay vì dồn hết vào 1 timestamp.

  Sóng sinh hoạt cuối tuần (Weekend Traffic Spike):
  Nếu ngày đang giả lập rơi vào Thứ Bảy/Chủ Nhật, biên độ VIEW_MAX và
  LIKE_MAX được nhân lên (xem WEEKEND_MULTIPLIER) để mô phỏng traffic
  tăng vọt cuối tuần — giúp biểu đồ uốn lượn chân thực hơn.

Raw log có user_id (movie_view_logs) — BỔ SUNG MỚI
─────────────────────────────────────────────────────────
  Mỗi sự kiện "view" giả lập (đúng số lượng n_views, đúng timestamp đã
  sinh cho ES) giờ CŨNG được tạo thêm 1 dòng MovieViewLogModel, ghi vào
  bảng movie_view_logs (PostgreSQL analytics DB) — cùng bảng mà task
  thật flush_view_logs_buffer ghi vào từ luồng Write-Behind Redis buffer
  thật. user_id được gán ngẫu nhiên từ SIMULATED_USER_POOL (hoặc
  "anonymous" theo ANONYMOUS_VIEW_RATIO) vì đây là dữ liệu giả lập, không
  có người dùng thật đứng sau mỗi lượt xem.

  episode_id cũng được random THẬT từ bảng episode (join theo movie_id đã
  bốc, xem episodes_by_movie bên dưới) — không bịa chuỗi ngẫu nhiên, để
  không phá vỡ tính toàn vẹn dữ liệu. Phim nào chưa có episode trong DB
  thì episode_id vẫn là None, không lỗi.

  KHÔNG ảnh hưởng gì tới movie_daily_statistics: bảng đó vẫn chỉ do
  aggregate_task.py tổng hợp từ ES như cũ, không đọc gì từ
  movie_view_logs cả — nên phần bổ sung này chỉ tạo thêm dữ liệu test
  cho raw log, không tạo nguy cơ đếm trùng nào mới.
"""

import logging
import os
import random
from datetime import datetime, timedelta, timezone

import redis
from sqlalchemy import func
from elasticsearch.helpers import bulk 

from src.infrastructure.database.models.movies.movie_model import EpisodeModel, MovieModel
from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.elasticsearch.es_client import es_client  # 🔥 Sử dụng es_client chung
from src.infrastructure.database.analytics_session import AnalyticsSessionLocal
from src.infrastructure.database.models.analytics.movie_view_log import MovieViewLogModel

logger = logging.getLogger(__name__)

# ── Redis sync client (db=1, tách biệt khỏi Celery broker db=0) ──────────────
_redis = redis.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/1"),
    decode_responses=True,
)

POOL_SIZE = 20
PICK_MIN  = 5
PICK_MAX  = 10

# Biên độ ngày THƯỜNG (Thứ 2 → Thứ 6) — giữ nguyên như code gốc.
VIEW_MIN  = 0
VIEW_MAX  = 500
LIKE_MIN  = 0
LIKE_MAX  = 50

# Hệ số nhân biên độ MAX cho ngày CUỐI TUẦN (Thứ 7, Chủ Nhật).
# VIEW_MAX 500 → 1000, LIKE_MAX 50 → 100 khi multiplier = 2.0.
WEEKEND_MULTIPLIER = 2.0

# ── Giả lập user_id cho movie_view_logs (raw log có định danh người xem) ────
SIMULATED_USER_POOL  = [f"anonymous_{i:03d}" for i in range(1, 1000)]  # 30 user giả lập
ANONYMOUS_VIEW_RATIO = 0.2  # 20% lượt xem giả lập là khách vãng lai (chưa đăng nhập)

DURATION_WATCHED_MIN = 30    # giây
DURATION_WATCHED_MAX = 7200  # giây (~2 tiếng, đủ cho phim dài)


def _pick_simulated_user_id() -> str:
    """Trả về user_id giả lập, hoặc 'anonymous' theo tỉ lệ ANONYMOUS_VIEW_RATIO."""
    if random.random() < ANONYMOUS_VIEW_RATIO:
        return "anonymous"
    return random.choice(SIMULATED_USER_POOL)


@celery_instance.task(
    bind=True,
    name="tasks.simulate_user_traffic",
    max_retries=2,
    default_retry_delay=60,
    queue="light_queue",
    acks_late=True,
)
def task_simulate_user_traffic(self, days_back: int = 1):
    """
    Giả lập traffic người dùng, có thể chạy 1 ngày (chu kỳ 5 phút bình
    thường) hoặc backfill nhiều ngày liên tiếp trong quá khứ.

    Tham số:
        days_back (int): Số ngày cần sinh dữ liệu, tính lùi từ hôm qua.
            - days_back = 1 (mặc định): chỉ sinh dữ liệu NGÀY HÔM QUA
              (giữ nguyên hành vi cũ, an toàn cho lịch chạy tự động).
            - days_back > 1: lặp cuốn chiếu từ "days_back ngày trước"
              cho tới "hôm qua", sinh dữ liệu đầy đủ cho từng ngày.

    Với MỖI ngày trong phạm vi backfill:
      1. Bốc ngẫu nhiên 5–10 phim đang hoạt động từ MySQL.
      2. Xác định ngày đó là ngày thường hay cuối tuần → chọn biên độ
         random view/like tương ứng (cuối tuần nhân lên theo
         WEEKEND_MULTIPLIER).
      3. Pipeline Redis INCRBY — tăng view và like ảo phục vụ xả đệm MySQL.
      4. Bulk đúc dữ liệu tương tác thô (view/like) của ngày đó ném vào
         Elasticsearch, với timestamp ngẫu nhiên (h, m, s) trong đúng
         ngày đang giả lập.
      5. Bulk insert raw log (có user_id + episode_id giả lập) vào
         PostgreSQL bảng movie_view_logs — 1 dòng cho mỗi sự kiện "view"
         đã sinh ở bước 4, cùng timestamp, phục vụ test tính năng ghi
         nhận lượt xem thật.
    """
    if days_back < 1:
        days_back = 1

    db = SessionLocal()
    try:
        movies = (
            db.query(MovieModel.id, MovieModel.name)
            .filter(MovieModel.is_deleted == False)
            .order_by(func.rand())          # MySQL: RAND(); PostgreSQL: RANDOM()
            .limit(POOL_SIZE)
            .all()
        )

        # Lấy toàn bộ episode của các phim vừa bốc, gom theo movie_id, để
        # random episode_id chân thực khi sinh raw log (thay vì luôn None).
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

    now = datetime.now(timezone.utc)

    total_views  = 0
    total_likes  = 0
    total_logged = 0
    daily_breakdown = []

    db_analytics = AnalyticsSessionLocal()
    try:
        # 💡 Lặp cuốn chiếu từ "days_back ngày trước" cho tới "hôm qua".
        # days_back=1 → chỉ 1 vòng lặp với offset=1 (hôm qua), y hệt logic cũ.
        for day_offset in range(days_back, 0, -1):
            target_date = now - timedelta(days=day_offset)
            is_weekend  = target_date.weekday() in (5, 6) 

            if is_weekend:
                day_view_min, day_view_max = VIEW_MIN, int(VIEW_MAX * WEEKEND_MULTIPLIER)
                day_like_min, day_like_max = LIKE_MIN, int(LIKE_MAX * WEEKEND_MULTIPLIER)
            else:
                day_view_min, day_view_max = VIEW_MIN, VIEW_MAX
                day_like_min, day_like_max = LIKE_MIN, LIKE_MAX

            # ── Bước 1 (cho ngày này): Sample 5–10 phim từ pool ─────────────
            k      = random.randint(PICK_MIN, PICK_MAX)
            picked = random.sample(movies, min(k, len(movies)))

            # ── Bước 2 (cho ngày này): Hạ tầng nạp dữ liệu Redis + ES + PG ──
            day_views  = 0
            day_likes  = 0
            es_actions = []  # Mảng chứa danh sách tài liệu log thô của riêng ngày này
            view_log_rows = []  # Raw log có user_id, ghi vào movie_view_logs (PostgreSQL)

            pipe = _redis.pipeline(transaction=False)

            for movie in picked:
                n_views = random.randint(day_view_min, day_view_max)
                n_likes = random.randint(day_like_min, day_like_max)

                # 🛠️ Hành động 1: Tích lũy vào RAM Redis db=1 phục vụ luồng xả đệm MySQL cũ
                pipe.incrby(f"view:{movie.id}", n_views)
                pipe.incrby(f"like:{movie.id}", n_likes)

                day_views += n_views
                day_likes += n_likes

                movie_episodes = episodes_by_movie.get(movie.id)

                # 🛠️ Hành động 2: Chuẩn bị mẻ log thô ném sang Elasticsearch
                # Tạo các bản ghi sự kiện View — ĐỒNG THỜI sinh raw log có
                # user_id + episode_id cho movie_view_logs, dùng chung
                # timestamp ts để 2 nguồn dữ liệu khớp nhau khi đối chiếu.
                for _ in range(n_views):
                    # Sinh giờ, phút, giây ngẫu nhiên trong ĐÚNG ngày đang giả lập
                    h = random.randint(0, 23)
                    m = random.randint(0, 59)
                    s = random.randint(0, 59)
                    ts = datetime(
                        target_date.year, target_date.month, target_date.day,
                        h, m, s, tzinfo=timezone.utc,
                    )

                    es_actions.append({
                        "_index": "movie_interactions_log",
                        "_source": {
                            "movie_id": str(movie.id),
                            "action": "view",
                            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),  # Định dạng khớp strict_date_hour_minute_second
                        }
                    })

                    view_log_rows.append(MovieViewLogModel(
                        user_id=_pick_simulated_user_id(),
                        movie_id=str(movie.id),
                        episode_id=random.choice(movie_episodes) if movie_episodes else None,
                        duration_watched=random.randint(DURATION_WATCHED_MIN, DURATION_WATCHED_MAX),
                        created_at=ts,
                    ))

                # Tạo các bản ghi sự kiện Like
                for _ in range(n_likes):
                    h = random.randint(0, 23)
                    m = random.randint(0, 59)
                    s = random.randint(0, 59)
                    ts = datetime(
                        target_date.year, target_date.month, target_date.day,
                        h, m, s, tzinfo=timezone.utc,
                    )

                    es_actions.append({
                        "_index": "movie_interactions_log",
                        "_source": {
                            "movie_id": str(movie.id),
                            "action": "like",
                            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                        }
                    })

            # Thực thi đẩy bộ đếm sang Redis (1 Round-trip cho ngày này)
            pipe.execute()

            # 🚀 Tiến hành thực thi đẩy mẻ log thô của ngày này sang Elasticsearch
            if es_actions:
                success_count, failed = bulk(es_client, es_actions)
                logger.info(
                    "[SimTraffic] Ngày %s (%s): bulk sync thành công %d tài liệu log thô vào ES 'movie_interactions_log' ✓",
                    target_date.date().isoformat(),
                    "cuối tuần" if is_weekend else "ngày thường",
                    success_count,
                )
                if failed:
                    logger.error(
                        "[SimTraffic] Ngày %s: số bản ghi bulk thất bại: %d",
                        target_date.date().isoformat(), len(failed),
                    )

            # 🚀 Bulk insert raw log (có user_id + episode_id) của ngày này vào PostgreSQL
            if view_log_rows:
                db_analytics.bulk_save_objects(view_log_rows)
                db_analytics.commit()
                logger.info(
                    "[SimTraffic] Ngày %s: đã bulk insert %d dòng movie_view_logs (raw log, có user_id) ✓",
                    target_date.date().isoformat(), len(view_log_rows),
                )
                total_logged += len(view_log_rows)

            total_views += day_views
            total_likes += day_likes
            daily_breakdown.append({
                "date":        target_date.date().isoformat(),
                "is_weekend":  is_weekend,
                "picked":      len(picked),
                "views_added": day_views,
                "likes_added": day_likes,
                "view_logs_inserted": len(view_log_rows),
                "movies":      [mv.name for mv in picked],
            })

    except Exception as exc:
        db_analytics.rollback()
        logger.exception("[SimTraffic] Hệ thống đường ống (Pipeline) gặp lỗi: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db_analytics.close()

    result = {
        "days_back":       days_back,
        "days_processed":  len(daily_breakdown),
        "views_added":     total_views,
        "likes_added":     total_likes,
        "view_logs_inserted": total_logged,
        "daily_breakdown": daily_breakdown,
    }
    logger.info("[SimTraffic] Hoàn tất chu kỳ giả lập (%d ngày): %s", len(daily_breakdown), result)
    return result