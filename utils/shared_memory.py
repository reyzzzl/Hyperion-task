import asyncio
import json
from typing import Any, Dict, Optional
from datetime import datetime
from .redis_client import get_redis_client

_redis_lock = asyncio.Lock()

class SharedMemory:
    def __init__(self):
        self._in_memory: Dict[str, Any] = {}
        self._in_memory_ttl: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._redis = None

    async def _get_redis(self):
        if self._redis is not None:
            return self._redis
        async with _redis_lock:
            if self._redis is not None:
                return self._redis
            self._redis = await get_redis_client()
            return self._redis

    async def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None):
        redis = await self._get_redis()
        if redis:
            await redis.set(key, json.dumps(value), ex=int(ttl_seconds) if ttl_seconds else None)
            return
        async with self._lock:
            self._in_memory[key] = value
            if ttl_seconds:
                self._in_memory_ttl[key] = datetime.now().timestamp() + ttl_seconds

    async def get(self, key: str) -> Optional[Any]:
        redis = await self._get_redis()
        if redis:
            val = await redis.get(key)
            return json.loads(val) if val else None
        async with self._lock:
            now = datetime.now().timestamp()
            if key in self._in_memory_ttl and self._in_memory_ttl[key] < now:
                del self._in_memory[key]
                del self._in_memory_ttl[key]
                return None
            return self._in_memory.get(key)

    async def delete(self, key: str):
        redis = await self._get_redis()
        if redis:
            await redis.delete(key)
            return
        async with self._lock:
            self._in_memory.pop(key, None)
            self._in_memory_ttl.pop(key, None)

    async def clear(self):
        redis = await self._get_redis()
        if redis:
            await redis.flushdb()
            return
        async with self._lock:
            self._in_memory.clear()
            self._in_memory_ttl.clear()