

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ANALYTICS_DATABASE_URL = os.getenv(
    "ANALYTICS_DATABASE_URL",
    "postgresql+psycopg2://postgres:Kute12345@postgres:5432/movie_analytics",
)

analytics_engine = create_engine(
    ANALYTICS_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  
    pool_recycle=1800,
    echo=False,
)


class AnalyticsBase(DeclarativeBase):
    pass


AnalyticsSessionLocal = sessionmaker(
    bind=analytics_engine,
    autocommit=False,
    autoflush=False,
)


def get_analytics_db():
    """FastAPI Dependency — inject analytics session vào router."""
    db = AnalyticsSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_analytics_tables():
    """
    Tạo toàn bộ bảng analytics trong PostgreSQL.
    Gọi hàm này 1 lần khi khởi động app (xem main.py bên dưới).
    """
    AnalyticsBase.metadata.create_all(bind=analytics_engine)
    print("[Analytics] PostgreSQL tables created ✓")