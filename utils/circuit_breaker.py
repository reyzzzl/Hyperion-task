import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional
from .exceptions import CircuitOpenError

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0, half_open_max_calls: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                else:
                    raise CircuitOpenError(f"Circuit breaker '{self.name}' is OPEN")
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure()
            raise e

    async def _record_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    async def _record_failure(self):
        async with self._lock:
            self.last_failure_time = time.monotonic()
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
                if self.half_open_calls >= self.half_open_max_calls:
                    self.state = CircuitState.OPEN
            elif self.state == CircuitState.CLOSED:
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN

    def get_state(self) -> str:
        return self.state.value