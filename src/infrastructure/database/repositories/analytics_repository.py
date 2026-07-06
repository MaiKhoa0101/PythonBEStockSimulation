# src/infrastructure/repositories/analytics_repository.py
"""
Repository dùng 2 session:
  - self.db       → PostgreSQL (analytics)  — query MovieDailyStatistic
  - self.db_mysql → MySQL (main)            — query MovieModel, CategoryModel
                                              (genres_distribution)
"""

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.application.interfaces.repositories.analytics_repository_interface import IAnalyticsRepository
from src.infrastructure.database.models.analytics.movie_daily_statistic import MovieDailyStatistic
from src.infrastructure.database.models.movies.movie_model import MovieModel
from src.infrastructure.database.models.associations.associations import (
    movie_category_association,
)


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
            query = query.filter(MovieDailyStatistic.date <= end_date)

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

    # ── Views Overview (PostgreSQL) ───────────────────────────────────────────
    def get_views_overview(
        self,
        start_date: Optional[date],
        end_date:   Optional[date],
    ) -> List[dict]:
        query = (
            self.db.query(
                MovieDailyStatistic.date,
                func.sum(MovieDailyStatistic.views_count).label("total_views"),
                func.sum(MovieDailyStatistic.likes_count).label("total_likes"),
                func.sum(MovieDailyStatistic.click_count).label("total_clicks"),
            )
        )

        if start_date:
            query = query.filter(MovieDailyStatistic.date >= start_date)
        if end_date:
            query = query.filter(MovieDailyStatistic.date <= end_date)

        rows = (
            query
            .group_by(MovieDailyStatistic.date)
            .order_by(MovieDailyStatistic.date.asc())
            .all()
        )

        return [
            {
                "date":         r.date,
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
                  CategoryModel.id == movie_category_association.c.category_id)
            .join(MovieModel,
                  MovieModel.id == movie_category_association.c.movie_id)
            .filter(MovieModel.is_deleted == False)
            .group_by(CategoryModel.id, CategoryModel.name)
            .order_by(func.count(MovieModel.id).desc())
            .all()
        )

        return [{"label": r.label, "value": r.value} for r in rows]