# src/infrastructure/database/models/analytics/movie_daily_statistic.py
"""
LƯU Ý VỀ THIẾT KẾ (đã đổi so với bản gốc):

Trước đây mỗi dòng = tổng cả NGÀY của 1 phim (1 dòng/phim/ngày).
Bây giờ mỗi dòng = tổng của 1 BUCKET THỜI GIAN (mặc định: 1 giờ) của 1 phim
(nhiều dòng/phim/ngày). Nhờ vậy khi query có thể dùng date_trunc() để gom
lại theo phút / giờ / ngày / tuần / tháng tuỳ ý — xem analytics_repository.py.

Giới hạn: không thể gom MỊN HƠN độ phân giải lúc ghi. Nếu cần chính xác tới
từng phút, đổi AGG_INTERVAL trong aggregate_task.py thành "minute" (sẽ sinh
ra nhiều dòng hơn hẳn — cân nhắc khối lượng dữ liệu trước khi đổi).
"""

import uuid

from sqlalchemy import BigInteger, Column, DateTime, String, UniqueConstraint

from src.infrastructure.database.analytics_session import AnalyticsBase


class MovieDailyStatistic(AnalyticsBase):
    __tablename__ = "movie_daily_statistics"

    __table_args__ = (
        # Mỗi phim chỉ có đúng 1 bản ghi cho mỗi bucket thời gian
        UniqueConstraint("movie_id", "date", name="uq_movie_date"),
    )

    id          = Column(String(50),  primary_key=True,
                         default=lambda: str(uuid.uuid4()))
    movie_id    = Column(String(255), nullable=False, index=True,
                         comment="FK tham chiếu tới movie.id bên MySQL")
    date        = Column(DateTime(timezone=True), nullable=False, index=True,
                         comment="Thời điểm bắt đầu bucket, vd: 2026-07-07 14:00:00+00")
    views_count = Column(BigInteger, nullable=False, default=0,
                         comment="Lượt xem trong bucket")
    likes_count = Column(BigInteger, nullable=False, default=0,
                         comment="Lượt thích trong bucket")
    click_count = Column(BigInteger, nullable=False, default=0,
                         comment="Lượt click trong bucket")

    def __repr__(self):
        return (
            f"<MovieDailyStatistic movie={self.movie_id!r}"
            f" date={self.date} views={self.views_count}>"
        )