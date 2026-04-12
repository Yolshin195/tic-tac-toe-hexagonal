from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator


DATABASE_URL = "sqlite+aiosqlite:///./tic_tac_toe.db"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session