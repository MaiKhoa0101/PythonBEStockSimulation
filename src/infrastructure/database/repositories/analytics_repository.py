# src/infrastructure/repositories/analytics_repository.py
"""
Repository dùng 2 session:
  - self.db       → PostgreSQL (analytics)  — query MovieDailyStatistic
  - self.db_mysql → MySQL (main)            — query MovieModel, CategoryModel
                                              (genres_distribution)
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Literal, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.infrastructure.database.models.categories.categories import CategoryModel
from src.application.interfaces.repositories.analytics_repository_interface import IAnalyticsRepository
from src.infrastructure.database.models.analytics.movie_daily_statistic import MovieDailyStatistic
from src.infrastructure.database.models.movies.movie_model import MovieModel
from src.infrastructure.database.models.associations.associations import (
    movie_category_association,
)

from dateutil.relativedelta import relativedelta
from src.infrastructure.database.models.transaction.transaction_model import TransactionModel
from src.infrastructure.database.models.users.user_model import UserModel
from src.infrastructure.database.session import SessionLocal
from src.domain.entities.analytics_entity.analytics_entity import UserSubTrendPoint

Granularity = Literal["minute", "hour", "day", "week", "month"]
_VALID_GRANULARITIES = {"minute", "hour", "day", "week", "month"}
_ALLOWED_GRANULARITY = {"day", "week", "month"}


def _parse_date(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} không hợp lệ, cần định dạng YYYY-MM-DD") from exc


def _generate_buckets(start: date, end: date, granularity: str) -> List[date]:
    """Sinh dãy mốc thời gian LIÊN TỤC từ start -> end theo granularity,
    để biểu đồ không bị đứt gãy tại những khoảng thời gian không có dữ liệu
    (những bucket không có bản ghi nào sẽ được điền 0 thay vì biến mất khỏi mảng).
    """
    buckets: List[date] = []
    current = start

    if granularity == "day":
        step = relativedelta(days=1)
    elif granularity == "week":
        current = current - relativedelta(days=current.weekday())
        step = relativedelta(weeks=1)
    else:  # month
        current = current.replace(day=1)
        step = relativedelta(months=1)

    while current <= end:
        buckets.append(current)
        current = current + step

    return buckets


def _bucket_key(d: date, granularity: str) -> date:
    """Quy 1 ngày cụ thể về mốc bucket (đầu tuần / đầu tháng).

    Dùng để gộp kết quả group-by-NGÀY (chạy được cả Postgres lẫn MySQL vì
    dùng func.date(), không phải func.date_trunc() — hàm chỉ Postgres có)
    lên granularity week/month ngay ở tầng Python, thay vì phải viết riêng
    biểu thức SQL cho từng dialect.
    """
    if granularity == "week":
        return d - timedelta(days=d.weekday())
    if granularity == "month":
        return d.replace(day=1)
    return d



class AnalyticsRepository(IAnalyticsRepository):

    def __init__(self, db: Session, db_mysql: Session):
        self.db       = db        # PostgreSQL session
        self.db_mysql = db_mysql  # MySQL session

    # ── Top Trending (PostgreSQL) ─────────────────────────────────────────────
    def get_top_trending(
        self,
        start_date: Optional[date],
        end_date:   Optional[date],
        page:       int,
        size:       int,
    ) -> Tuple[List[dict], int]:
        views_sum  = func.sum(MovieDailyStatistic.views_count).label("views_count")
        likes_sum  = func.sum(MovieDailyStatistic.likes_count).label("likes_count")
        clicks_sum = func.sum(MovieDailyStatistic.click_count).label("click_count")

        # Lấy tên phim từ MySQL bằng subquery trên PostgreSQL
        # (movie_id là FK logic — không có DB-level FK vì 2 DB khác nhau)
        query = (
            self.db.query(
                MovieDailyStatistic.movie_id,
                views_sum,
                likes_sum,
                clicks_sum,
            )
        )

        if start_date:
            query = query.filter(MovieDailyStatistic.date >= start_date)
        if end_date:

            query = query.filter(MovieDailyStatistic.date < end_date + timedelta(days=1))

        query = query.group_by(MovieDailyStatistic.movie_id)

        total = query.count()

        rows = (
            query
            .order_by(views_sum.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        # Enrich tên phim từ MySQL
        movie_ids  = [r.movie_id for r in rows]
        movie_map  = {}
        if movie_ids:
            movies = (
                self.db_mysql.query(MovieModel.id, MovieModel.name)
                .filter(MovieModel.id.in_(movie_ids))
                .all()
            )
            movie_map = {m.id: m.name for m in movies}

        result = [
            {
                "movie_id":    r.movie_id,
                "movie_title": movie_map.get(r.movie_id),
                "views_count": r.views_count or 0,
                "likes_count": r.likes_count or 0,
                "click_count": r.click_count or 0,
            }
            for r in rows
        ]

        return result, total

    def get_views_overview(
        self,
        start_date:  Optional[date],
        end_date:    Optional[date],
        granularity: Granularity = "day",
    ) -> List[dict]:

        if granularity not in _VALID_GRANULARITIES:
            raise ValueError(f"granularity không hợp lệ: {granularity!r}")

        bucket = func.date_trunc(granularity, MovieDailyStatistic.date).label("bucket")

        query = self.db.query(
            bucket,
            func.sum(MovieDailyStatistic.views_count).label("total_views"),
            func.sum(MovieDailyStatistic.likes_count).label("total_likes"),
            func.sum(MovieDailyStatistic.click_count).label("total_clicks"),
        )

        if start_date:
            query = query.filter(MovieDailyStatistic.date >= start_date)
        if end_date:
            # Cùng bug như get_top_trending — xem giải thích ở đó.
            query = query.filter(MovieDailyStatistic.date < end_date + timedelta(days=1))

        rows = (
            query
            .group_by(bucket)
            .order_by(bucket.asc())
            .all()
        )

        return [
            {
                "date":         r.bucket,
                "total_views":  r.total_views  or 0,
                "total_likes":  r.total_likes  or 0,
                "total_clicks": r.total_clicks or 0,
            }
            for r in rows
        ]

    def get_genres_distribution(self) -> List[dict]:
        """
        Chạy hoàn toàn trên MySQL — không cần PostgreSQL.
        Đếm số phim đang hoạt động theo từng thể loại.
        """
        rows = (
            self.db_mysql.query(
                CategoryModel.name.label("label"),
                func.count(MovieModel.id).label("value"),
            )
            .join(movie_category_association,
                  CategoryModel.id == movie_category_association.c.id_category)
            .join(MovieModel,
                  MovieModel.id == movie_category_association.c.id_movie)
            .filter(MovieModel.is_deleted == False)
            .group_by(CategoryModel.id, CategoryModel.name)
            .order_by(func.count(MovieModel.id).desc())
            .all()
        )

        return [{"label": r.label, "value": r.value} for r in rows]
    
    def fetch_user_subscription_trends(
        self, start_date: str, end_date: str, granularity: str
    ) -> List[UserSubTrendPoint]:
        if granularity not in _ALLOWED_GRANULARITY:
            raise ValueError(
                f"granularity không hợp lệ: '{granularity}'. Chỉ chấp nhận: {sorted(_ALLOWED_GRANULARITY)}"
            )

        start = _parse_date(start_date, "startDate")
        end = _parse_date(end_date, "endDate")
        if start > end:
            raise ValueError("startDate phải nhỏ hơn hoặc bằng endDate")

        try:
            day_col_user = func.date(UserModel.created_at).label("bucket")
            users_rows = (
                self.db_mysql.query(
                    day_col_user,
                    func.count(UserModel.id).label("cnt"),
                )
                .filter(
                    UserModel.is_deleted.is_(False),
                    UserModel.created_at >= start,
                    UserModel.created_at < end + relativedelta(days=1),
                )
                .group_by(day_col_user)
                .all()
            )

            day_col_tx = func.date(TransactionModel.created_at).label("bucket")

            subs_rows = (
                self.db_mysql.query(
                    day_col_tx,
                    func.count(TransactionModel.id).label("cnt"),
                )
                .filter(
                    TransactionModel.status == "SUCCESS",
                    TransactionModel.created_at >= start,
                    TransactionModel.created_at < end + relativedelta(days=1),
                )
                .group_by(day_col_tx)
                .all()
            )

            unsubs_rows = (
                self.db_mysql.query(
                    day_col_tx,
                    func.count(TransactionModel.id).label("cnt"),
                )
                .filter(
                    TransactionModel.status.in_(["REFUNDED", "CANCELED"]),
                    TransactionModel.created_at >= start,
                    TransactionModel.created_at < end + relativedelta(days=1),
                )
                .group_by(day_col_tx)
                .all()
            )
        except Exception as exc:
            raise RuntimeError(
                "Không lấy được dữ liệu user subscription trends từ MySQL"
            ) from exc

        def _to_bucket_map(rows) -> Dict[date, int]:
            agg: Dict[date, int] = {}
            for row in rows:
                raw_day = row.bucket if isinstance(row.bucket, date) else row.bucket.date()
                key = _bucket_key(raw_day, granularity)
                agg[key] = agg.get(key, 0) + row.cnt
            return agg

        users_map = _to_bucket_map(users_rows)
        subs_map = _to_bucket_map(subs_rows)
        unsubs_map = _to_bucket_map(unsubs_rows)

        # ── Merge theo key ngày tháng, điền 0 cho bucket trống ──────────
        buckets = _generate_buckets(start, end, granularity)
        return [
            UserSubTrendPoint(
                bucket_date=bucket,
                new_users=users_map.get(bucket, 0),
                new_subscriptions=subs_map.get(bucket, 0),
                unsubscriptions=unsubs_map.get(bucket, 0),
            )
            for bucket in buckets
        ]