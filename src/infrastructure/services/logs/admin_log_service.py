import json
import logging
from typing import Any, Optional

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