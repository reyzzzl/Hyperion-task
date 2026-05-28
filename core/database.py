import asyncio
import logging
import os
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

logger = logging.getLogger("Database")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/hyperion")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "timeout": 30,
        "command_timeout": 30,
    },
    echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def init_db_with_retry(max_retries: int = 5, delay: float = 2.0):
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return
        except OperationalError as e:
            logger.warning("DB connection failed (attempt %d/%d): %s", attempt, max_retries, str(e))
            if attempt < max_retries:
                await asyncio.sleep(delay)
            else:
                raise RuntimeError("Could not connect to database after retries") from e

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session