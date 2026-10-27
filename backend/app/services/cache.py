import json
from importlib import import_module
from typing import Dict, Any
import os
import time


class _MemoryRedis:
    """Small process-local fallback for environments without redis-py."""

    def __init__(self) -> None:
        self._values: Dict[str, tuple[bytes, float]] = {}

    async def get(self, key: str) -> bytes | None:
        entry = self._values.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() >= expires_at:
            self._values.pop(key, None)
            return None
        return value

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self._values[key] = (value.encode(), time.monotonic() + seconds)


# Initialize Redis when redis-py is installed; otherwise use a local fallback.
try:
    redis = import_module("redis.asyncio")
except ModuleNotFoundError:
    redis_client = _MemoryRedis()
else:
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

async def get_revenue_summary(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    """
    cache_key = f"revenue:{tenant_id}:{property_id}"
    
    # Try to get from cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    
    # Calculate revenue
    result = await calculate_total_revenue(property_id, tenant_id)
    
    # Cache the result for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result
