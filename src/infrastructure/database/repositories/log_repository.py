from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.application.interfaces.repositories.log_repository_interface import ILogRepository
from src.infrastructure.database.models.celery_task_log.celery_task_log import CeleryTaskLog


class LogRepository(ILogRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_paginated(
        self,
        page: int,
        size: int,
        status: Optional[str] = None,
        name: Optional[str] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        updated_from: Optional[datetime] = None,
        updated_to: Optional[datetime] = None,
    ) -> Tuple[List[CeleryTaskLog], int]:
        query = self.db.query(CeleryTaskLog)

        if status:
            query = query.filter(CeleryTaskLog.status == status)
        if name:
            query = query.filter(CeleryTaskLog.name.ilike(f"%{name}%"))

        # Lọc theo khoảng thời gian "Tạo lúc"
        if created_from:
            query = query.filter(CeleryTaskLog.created_at >= created_from)
        if created_to:
            query = query.filter(CeleryTaskLog.created_at <= created_to)

        # Lọc theo khoảng thời gian "Cập nhật"
        if updated_from:
            query = query.filter(CeleryTaskLog.updated_at >= updated_from)
        if updated_to:
            query = query.filter(CeleryTaskLog.updated_at <= updated_to)

        total = query.count()

        items = (
            query.order_by(CeleryTaskLog.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return items, total

    def get_by_id(self, task_id: str) -> Optional[CeleryTaskLog]:
        return self.db.query(CeleryTaskLog).filter(CeleryTaskLog.id == task_id).first()

    def count_by_status(self) -> Dict[str, int]:
        rows = (
            self.db.query(CeleryTaskLog.status, func.count(CeleryTaskLog.id))
            .group_by(CeleryTaskLog.status)
            .all()
        )
        return {status: count for status, count in rows}