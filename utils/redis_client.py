import asyncio
import json
import os
from typing import Any, Optional

_redis_client = None

async def get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis.asyncio as aioredis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        _redis_client = await aioredis.from_url(redis_url, decode_responses=True)
        await _redis_client.ping()
        return _redis_client
    except Exception:
        return None