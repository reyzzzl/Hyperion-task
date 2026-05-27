import asyncio
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional

logger = logging.getLogger("Retry")

def retry(exceptions: Tuple[Type[Exception], ...], max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, jitter: float = 0.1):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt == max_attempts - 1:
                        break
                    await asyncio.sleep(current_delay + (jitter * (attempt + 1)))
                    current_delay *= backoff
            raise last_exc
        return wrapper
    return decorator