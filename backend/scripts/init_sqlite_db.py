"""Initialize SQLite database directly using SQLModel metadata.

This bypasses Alembic migrations which are PostgreSQL-specific.
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import all models to register them in metadata
from app import models  # noqa: F401
from app.core.config import settings


def _normalize_database_url(database_url: str) -> str:
    """Convert SQLite URL to async format."""
    if database_url.startswith("sqlite:///"):
        # Convert to async aiosqlite format
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return database_url


async def init_database() -> None:
    """Create all tables from SQLModel metadata."""
    database_url = _normalize_database_url(settings.database_url)
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    await engine.dispose()
    print(f"Database initialized successfully at: {settings.database_url}")


if __name__ == "__main__":
    asyncio.run(init_database())
