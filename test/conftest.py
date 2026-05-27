import pytest
import asyncio
from typing import AsyncGenerator

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def shared_memory():
    from hyperion_task.utils.shared_memory import SharedMemory
    mem = SharedMemory()
    yield mem
    await mem.clear()