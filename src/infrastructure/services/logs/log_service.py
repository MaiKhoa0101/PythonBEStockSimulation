import json
from typing import Dict, Optional

from src.application.interfaces.repositories.log_repository_interface import ILogRepository
from src.application.interfaces.services.log_service_interface import ILogService
from src.infrastructure.database.models.celery_task_log.celery_task_log import CeleryTaskLog


class LogService(ILogService):

    def __init__(self, log_repository: ILogRepository):
        self._repository = log_repository

    async def fetch_list(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        name: Optional[str] = None,
    ) -> dict:
        items, total = self._repository.get_paginated(page, size, status, name)
        total_pages = (total + size - 1) // size if size else 0

        return {
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "results": [self._serialize_summary(item) for item in items],
        }

    async def fetch_detail(self, task_id: str) -> Optional[dict]:
        log = self._repository.get_by_id(task_id)
        return self._serialize_detail(log) if log else None

    async def fetch_status_summary(self) -> Dict[str, int]:
        return self._repository.count_by_status()

    @staticmethod
    def _serialize_summary(log: CeleryTaskLog) -> dict:
        """Dùng cho danh sách (list view) — đủ thông tin hiển thị bảng."""
        return {
            "id": log.id,
            "root_id": log.root_id,
            "parent_id": log.parent_id,
            "name": log.name,
            "status": log.status,
            "count_retry": log.count_retry,
            "error": log.error,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None,
        }

    @staticmethod
    def _safe_json_loads(raw: Optional[str]):
        """args/kwargs lưu dạng JSON string trong DB — parse lại để trả JSON thật cho FE."""
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw 

    @classmethod
    def _serialize_detail(cls, log: CeleryTaskLog) -> dict:
        """Dùng cho trang chi tiết — bổ sung args/kwargs đã parse."""
        base = cls._serialize_summary(log)
        base["args"] = cls._safe_json_loads(log.args)
        base["kwargs"] = cls._safe_json_loads(log.kwargs)
        return base