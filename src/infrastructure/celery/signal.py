# src/infrastructure/celery/signals.py

import json
import logging
import os
import traceback as tb_module
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi_cache import FastAPICache
from redis.asyncio import Redis as AsyncRedis
from fastapi_cache.backends.redis import RedisBackend
from celery.signals import task_failure, task_prerun, task_retry, task_success, worker_process_init
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from src.infrastructure.database.models.celery_task_log.celery_task_log import CeleryTaskLog

logger = logging.getLogger(__name__)

_engine = create_engine(
    os.getenv("SQLALCHEMY_DATABASE_URL"),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   
    pool_recycle=1800,  
    echo=False,
)

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
        _ScopedSession.remove() 
def _to_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


@task_prerun.connect
def on_task_prerun(sender, task_id: str, task, args: tuple, kwargs: dict, **_):
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


@worker_process_init.connect
def on_worker_process_init(**kwargs):

    print("⚡ [Hạ tầng Worker] Tiến trình Worker đã mở mắt! Khởi tạo FastAPICache toàn cục...")
    redis_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    redis_client = AsyncRedis.from_url(redis_url)
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")