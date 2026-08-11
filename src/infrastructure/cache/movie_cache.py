# src/infrastructure/cache/movie_cache.py
"""
Cache layer cho movie module.

Thay thế fastapi-cache2 bằng redis.asyncio.Redis trực tiếp:
- API tường minh (redis.get/set/delete), không có tầng abstract
  clear(namespace, key) mơ hồ gây bug positional-argument.
- Không phụ thuộc prefix tự động của FastAPICache.init(prefix=...)
  (prefix đó CHỈ áp dụng khi dùng decorator @cache, không áp dụng
  khi gọi backend.get/set thủ công — đây là nguyên nhân gây lệch
  prefix giữa các cache_key trong code cũ).
- get/set là best-effort: mọi lỗi Redis đều bị bắt và log lại,
  không bao giờ làm hỏng response của API.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

CACHE_PREFIX = "movie-cache"


# ─────────────────────────────────────────────────────────────────────────────
# Key builder — SINGLE SOURCE OF TRUTH cho mọi cache key của movie module.
# Không hardcode string key rải rác trong controller nữa.
# ─────────────────────────────────────────────────────────────────────────────

def movie_detail_key(slug_name: str) -> str:
    return f"{CACHE_PREFIX}:movie:detail:{slug_name}"


def movie_list_home_key() -> str:
    return f"{CACHE_PREFIX}:movie:list:home"


# ─────────────────────────────────────────────────────────────────────────────
# Safe wrappers — best-effort, không bao giờ raise ra ngoài
# ─────────────────────────────────────────────────────────────────────────────

async def cache_get_json(redis: Redis, key: str) -> Optional[Any]:
    """Đọc cache, trả None nếu miss HOẶC nếu Redis lỗi (coi như miss)."""
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        logger.warning("cache GET failed key=%s", key, exc_info=True)
        return None


async def cache_set_json(redis: Redis, key: str, value: Any, expire: int) -> None:
    """Ghi cache. Lỗi Redis bị nuốt có chủ đích (best-effort warm cache)."""
    try:
        await redis.set(key, json.dumps(value), ex=expire)
    except Exception:
        logger.warning("cache SET failed key=%s", key, exc_info=True)


async def cache_delete(redis: Redis, *keys: str) -> None:
    """Xóa 1 hoặc nhiều key chính xác (KHÔNG dùng pattern/namespace)."""
    if not keys:
        return
    try:
        await redis.delete(*keys)
    except Exception:
        logger.warning("cache DELETE failed keys=%s", keys, exc_info=True)

async def invalidate_movie_list_home_cache(redis):
    """Xoá toàn bộ cache các trang của /listhome (mọi page), 
    dùng khi có phim mới/sửa/xoá để tránh cache cũ tồn tại tới 120s."""
    pattern = f"{movie_list_home_key()}:page:*"
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break