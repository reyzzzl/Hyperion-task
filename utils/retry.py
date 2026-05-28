import asyncio
import logging
import random
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any, Union

logger = logging.getLogger("Retry")

def retry(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                    if on_retry:
                        on_retry(attempt, e)
                    jitter_value = random.uniform(-jitter, jitter) if jitter > 0 else 0
                    wait_time = current_delay + jitter_value
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} after {wait_time:.2f}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                    current_delay *= backoff
            raise last_exception
        return wrapper
    return decorator