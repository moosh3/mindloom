from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from mindloom.db.session import async_session_maker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            # Note: Commits should typically happen within the endpoint logic
            # await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Session is automatically closed by the async context manager
            pass
