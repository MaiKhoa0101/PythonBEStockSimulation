# src/infrastructure/database/models/analytics/movie_daily_statistic.py

import uuid

from sqlalchemy import Column, Date, Integer, String, UniqueConstraint

from src.infrastructure.database.analytics_session import AnalyticsBase


class MovieDailyStatistic(AnalyticsBase):
    __tablename__ = "movie_daily_statistics"

    __table_args__ = (
        # Mỗi phim chỉ có đúng 1 bản ghi mỗi ngày
        UniqueConstraint("movie_id", "date", name="uq_movie_date"),
    )

    id          = Column(String(50),  primary_key=True,
                         default=lambda: str(uuid.uuid4()))
    movie_id    = Column(String(255), nullable=False, index=True,
                         comment="FK tham chiếu tới movie.id bên MySQL")
    date        = Column(Date,        nullable=False, index=True,
                         comment="Ngày thống kê, vd: 2026-07-03")
    views_count = Column(Integer,     nullable=False, default=0,
                         comment="Lượt xem trong ngày")
    likes_count = Column(Integer,     nullable=False, default=0,
                         comment="Lượt thích trong ngày")
    click_count = Column(Integer,     nullable=False, default=0,
                         comment="Lượt click vào phim trong ngày")

    def __repr__(self):
        return (
            f"<MovieDailyStatistic movie={self.movie_id!r}"
            f" date={self.date} views={self.views_count}>"
        )