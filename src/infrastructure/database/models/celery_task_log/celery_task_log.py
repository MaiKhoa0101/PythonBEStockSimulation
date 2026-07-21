# src/infrastructure/database/models/celery_task_log.py

from datetime import datetime, timezone
import enum

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from src.infrastructure.database.session import Base


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    RETRY   = "RETRY"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class CeleryTaskLog(Base):
    __tablename__ = "celery_task_logs"

    id          = Column(String(255), primary_key=True,                    comment="Task ID do Celery sinh (UUID)")
    root_id     = Column(String(255), nullable=True,  index=True,          comment="ID task gốc trong workflow chain/group")
    parent_id   = Column(String(255), nullable=True,  index=True,          comment="ID task cha trực tiếp")
    name        = Column(String(255), nullable=False,  index=True,         comment="Tên task đã đăng ký, vd: tasks.sync_movie_to_es")
    args        = Column(Text,        nullable=True,                       comment="Positional args – JSON string")
    kwargs      = Column(Text,        nullable=True,                       comment="Keyword args – JSON string")
    status      = Column(String(50),  nullable=False,  index=True,
                         default=TaskStatus.PENDING.value,                 comment="PENDING | STARTED | RETRY | SUCCESS | FAILURE")
    error       = Column(Text,        nullable=True,                       comment="Stack trace đầy đủ khi FAILURE")
    count_retry = Column(Integer,     nullable=False,  default=0,          comment="Số lần task đã retry")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    def __repr__(self):
        return f"<CeleryTaskLog id={self.id!r} name={self.name!r} status={self.status!r}>"