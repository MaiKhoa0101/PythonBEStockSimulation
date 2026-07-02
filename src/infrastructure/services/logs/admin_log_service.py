import json
import logging
from typing import Any, Optional

from src.application.interfaces.repositories.admin_log_repository_interface import IAdminLogRepository
from src.infrastructure.database.models.admin.admin_action_log import AdminActionLog
from src.infrastructure.database.session import SessionLocal

logger = logging.getLogger(__name__)


# ── Serializer ───────────────────────────────────────────────────────────────

def _to_json(value: Any) -> Optional[str]:
    """Chuyển dict / dataclass / ORM object thành JSON string."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        data = (
            {k: v for k, v in value.__dict__.items() if not k.startswith("_")}
            if hasattr(value, "__dict__")
            else value
        )
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        return None


# ── Helper chính ─────────────────────────────────────────────────────────────

def write_audit_log(
    *,
    action: str,
    admin_id: str,
    admin_email: Optional[str] = None,
    movie_id: str,
    movie_title: Optional[str] = None,
    old_values: Any = None,
    new_values: Any = None,
) -> None:
    """
    Tự mở SessionLocal riêng → gọi được từ Controller mà KHÔNG cần
    truyền db hay thay đổi signature của bất kỳ Service nào.

    Không raise exception — lỗi ghi log không được crash request.
    """
    db = SessionLocal()
    try:
        log = AdminActionLog(
            admin_id=admin_id,
            admin_email=admin_email,
            action=action,
            movie_id=movie_id,
            movie_title=movie_title,
            old_values=_to_json(old_values),
            new_values=_to_json(new_values),
        )
        db.add(log)
        db.commit()
        logger.debug("[Audit] %s movie=%s by=%s", action, movie_id, admin_id)
    except Exception:
        db.rollback()
        logger.exception(
            "[Audit] Lỗi ghi log — action=%s movie_id=%s admin=%s",
            action, movie_id, admin_id,
        )
    finally:
        db.close()

import json
from typing import Dict, Optional

from src.application.interfaces.services.admin_log_service_interface import IAdminLogService


class AdminLogService(IAdminLogService):

    def __init__(self, admin_log_repository: IAdminLogRepository):
        self._repository = admin_log_repository

    async def fetch_list(
        self,
        page: int = 1,
        size: int = 20,
        action: Optional[str] = None,
        admin_id: Optional[str] = None,
        movie_id: Optional[str] = None,
    ) -> dict:
        models, total = self._repository.get_paginated(page, size, action, admin_id, movie_id)
        total_pages = (total + size - 1) // size if size else 0

        return {
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "results": [self._serialize(m) for m in models],
        }

    async def fetch_detail(self, log_id: str) -> Optional[dict]:
        model = self._repository.get_by_id(log_id)
        return self._serialize_detail(model) if model else None

    async def fetch_action_summary(self) -> Dict[str, int]:
        # Đảm bảo đủ 3 action dù bảng chưa có data
        base = {"CREATE": 0, "UPDATE": 0, "DELETE": 0}
        base.update(self._repository.count_by_action())
        return base

    # ── Serializers ──────────────────────────────────────────────────────────

    @staticmethod
    def _safe_json_loads(raw: Optional[str]):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    @staticmethod
    def _serialize(model: AdminActionLog) -> dict:
        return {
            "id":          model.id,
            "admin_id":    model.admin_id,
            "admin_email": model.admin_email,
            "action":      model.action,
            "movie_id":    model.movie_id,
            "movie_title": model.movie_title,
            "created_at":  model.created_at.isoformat() if model.created_at else None,
        }

    @classmethod
    def _serialize_detail(cls, model: AdminActionLog) -> dict:
        base = cls._serialize(model)
        base["old_values"] = cls._safe_json_loads(model.old_values)
        base["new_values"] = cls._safe_json_loads(model.new_values)
        return base