

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
load_dotenv()
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
    # Import model ở đây để đảm bảo nó đã đăng ký vào AnalyticsBase.metadata
    # TRƯỚC khi gọi create_all() — dù main.py có import hay không
    from src.infrastructure.database.models.analytics.movie_daily_statistic import MovieDailyStatistic  # noqa: F401

    AnalyticsBase.metadata.create_all(bind=analytics_engine)
    print("[Analytics] PostgreSQL tables created ✓")