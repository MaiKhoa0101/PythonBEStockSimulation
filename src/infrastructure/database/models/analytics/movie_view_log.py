from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from src.infrastructure.database.analytics_session import AnalyticsBase


class MovieViewLogModel(AnalyticsBase):
    __tablename__ = "movie_view_logs"

    id               = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id          = Column(String(64), nullable=True, index=True,
                              comment="'anonymous' nếu user chưa đăng nhập")
    movie_id         = Column(String(64), nullable=False, index=True)
    episode_id       = Column(String(64), nullable=True)
    duration_watched = Column(Integer, nullable=False, default=0,
                              comment="Số giây đã xem trong lượt này")
    created_at       = Column(DateTime(timezone=True), nullable=False,
                              default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return (
            f"<MovieViewLogModel movie={self.movie_id!r} user={self.user_id!r}"
            f" duration={self.duration_watched}>"
        )