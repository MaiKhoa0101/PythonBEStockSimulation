from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.application.interfaces.repositories.admin_log_repository_interface import IAdminLogRepository
from src.infrastructure.database.models.admin.admin_action_log import AdminActionLog

class AdminLogRepository(IAdminLogRepository):

    def __init__(self, db: Session):
        self.db = db

    def get_paginated(
        self,
        page: int,
        size: int,
        action: Optional[str] = None,
        admin_id: Optional[str] = None,
        movie_id: Optional[str] = None,
    ) -> Tuple[List[AdminActionLog], int]:
        query = self.db.query(AdminActionLog)

        if action:
            query = query.filter(AdminActionLog.action == action)
        if admin_id:
            query = query.filter(AdminActionLog.admin_id == admin_id)
        if movie_id:
            query = query.filter(AdminActionLog.movie_id == movie_id)

        total = query.count()
        items = (
            query.order_by(AdminActionLog.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return items, total

    def get_by_id(self, log_id: str) -> Optional[AdminActionLog]:
        return self.db.query(AdminActionLog).filter(AdminActionLog.id == log_id).first()

    def count_by_action(self) -> Dict[str, int]:
        rows = (
            self.db.query(AdminActionLog.action, func.count(AdminActionLog.id))
            .group_by(AdminActionLog.action)
            .all()
        )
        return {action: count for action, count in rows}