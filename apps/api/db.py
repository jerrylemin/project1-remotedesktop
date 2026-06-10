from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from apps.api.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_async_engine(settings.database_url, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from apps.api import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if engine.url.get_backend_name().startswith("sqlite"):
            columns = await conn.execute(text("PRAGMA table_info(machines)"))
            column_names = {row[1] for row in columns}
            if "enabled" not in column_names:
                await conn.execute(text("ALTER TABLE machines ADD COLUMN enabled BOOLEAN NOT NULL DEFAULT 1"))

