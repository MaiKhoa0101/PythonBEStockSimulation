from typing import Dict, List, Optional, Protocol, Tuple

from sqlalchemy.orm import Session

from src.infrastructure.database.models.celery_task_log.celery_task_log import CeleryTaskLog


class ILogRepository(Protocol):
    def get_paginated(
        self,
        db: Session,
        page: int,
        size: int,
        status: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Tuple[List[CeleryTaskLog], int]:
        """Trả về (danh sách record của trang hiện tại, tổng số record khớp filter)."""
        raise NotImplementedError

    def get_by_id(self, db: Session, task_id: str) -> Optional[CeleryTaskLog]:
        """Lấy chi tiết 1 task log theo Task ID."""
        raise NotImplementedError

    def count_by_status(self, db: Session) -> Dict[str, int]:
        """Đếm số lượng task theo từng trạng thái — phục vụ dashboard tổng quan."""
        raise NotImplementedError