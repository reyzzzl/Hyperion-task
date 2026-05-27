import asyncio
import time
from typing import Dict

class TokenBucket:
    def __init__(self, rate: float, capacity: float):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_and_acquire(self, tokens: float = 1.0, max_wait: float = 5.0) -> bool:
        start = time.monotonic()
        while True:
            if await self.acquire(tokens):
                return True
            if time.monotonic() - start > max_wait:
                return False
            await asyncio.sleep(0.1)

class RateLimiter:
    def __init__(self, default_rate: float = 10, default_capacity: float = 20):
        self._limiters: Dict[str, TokenBucket] = {}
        self.default_rate = default_rate
        self.default_capacity = default_capacity
        self._lock = asyncio.Lock()

    async def get_limiter(self, key: str) -> TokenBucket:
        async with self._lock:
            if key not in self._limiters:
                self._limiters[key] = TokenBucket(self.default_rate, self.default_capacity)
            return self._limiters[key]

    async def acquire(self, key: str, tokens: float = 1.0) -> bool:
        limiter = await self.get_limiter(key)
        return await limiter.acquire(tokens)

    async def wait_and_acquire(self, key: str, tokens: float = 1.0, max_wait: float = 5.0) -> bool:
        limiter = await self.get_limiter(key)
        return await limiter.wait_and_acquire(tokens, max_wait)