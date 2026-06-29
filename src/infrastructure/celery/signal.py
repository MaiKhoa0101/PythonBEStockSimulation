# src/infrastructure/celery/signals.py
"""
Tự động ghi log vòng đời Celery task vào bảng celery_task_logs.

Đăng ký bằng cách import file này trong celery_app.py:
    import src.infrastructure.celery.signals  # noqa: F401
"""

import json
import logging
import os
import traceback as tb_module
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from celery.signals import task_failure, task_prerun, task_retry, task_success
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from src.infrastructure.database.models.celery_task_log import CeleryTaskLog

logger = logging.getLogger(__name__)

# ── Engine đồng bộ riêng — không dùng chung async engine của FastAPI ─────────
_engine = create_engine(
    os.getenv("SQLALCHEMY_DATABASE_URL"),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # Tránh "MySQL server has gone away"
    pool_recycle=1800,    # < MySQL wait_timeout mặc định (28800s)
    echo=False,
)

# scoped_session: mỗi thread worker nhận Session riêng → thread-safe
_ScopedSession = scoped_session(
    sessionmaker(bind=_engine, autocommit=False, autoflush=False)
)


@contextmanager
def _session_ctx():
    session = _ScopedSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        _ScopedSession.remove()  # Trả connection về pool, xóa thread-local


def _to_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


@task_prerun.connect
def on_task_prerun(sender, task_id: str, task, args: tuple, kwargs: dict, **_):
    """INSERT lần đầu, UPDATE khi retry."""
    try:
        with _session_ctx() as session:
            log = session.get(CeleryTaskLog, task_id)

            if log is None:
                session.add(CeleryTaskLog(
                    id=task_id,
                    root_id=getattr(task.request, "root_id", None),
                    parent_id=getattr(task.request, "parent_id", None),
                    name=task.name,
                    args=_to_json(list(args)),
                    kwargs=_to_json(kwargs),
                    status="STARTED",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ))
            else:
                log.status     = "STARTED"
                log.args       = _to_json(list(args))
                log.kwargs     = _to_json(kwargs)
                log.updated_at = datetime.now(timezone.utc)
    except Exception:
        logger.exception("[Signal] prerun error — task_id=%s", task_id)


@task_success.connect
def on_task_success(sender, result: Any, **_):
    """task_success không cấp task_id trực tiếp — lấy từ sender.request."""
    task_id = getattr(sender.request, "id", None)
    if not task_id:
        return
    try:
        with _session_ctx() as session:
            log = session.get(CeleryTaskLog, task_id)
            if log:
                log.status     = "SUCCESS"
                log.updated_at = datetime.now(timezone.utc)
    except Exception:
        logger.exception("[Signal] success error — task_id=%s", task_id)


@task_failure.connect
def on_task_failure(sender, task_id: str, exception: Exception,
                    args: tuple, kwargs: dict, traceback, einfo, **_):
    """Ghi FAILURE + toàn bộ stack trace."""
    error_str = str(einfo) if einfo is not None else tb_module.format_exc()
    try:
        with _session_ctx() as session:
            log = session.get(CeleryTaskLog, task_id)
            if log:
                log.status     = "FAILURE"
                log.error      = error_str
                log.updated_at = datetime.now(timezone.utc)
            else:
                # Hiếm: task fail trước khi prerun kịp ghi (vd: import error)
                session.add(CeleryTaskLog(
                    id=task_id,
                    name=getattr(sender, "name", "unknown"),
                    args=_to_json(list(args)),
                    kwargs=_to_json(kwargs),
                    status="FAILURE",
                    error=error_str,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ))
    except Exception:
        logger.exception("[Signal] failure error — task_id=%s", task_id)


@task_retry.connect
def on_task_retry(sender, request, reason, einfo, **_):
    """Tăng count_retry, chuyển RETRY — task chưa bị kết thúc."""
    task_id = getattr(request, "id", None)
    if not task_id:
        return
    try:
        with _session_ctx() as session:
            log = session.get(CeleryTaskLog, task_id)
            if log:
                log.status      = "RETRY"
                log.count_retry += 1
                log.updated_at  = datetime.now(timezone.utc)
    except Exception:
        logger.exception("[Signal] retry error — task_id=%s", task_id)