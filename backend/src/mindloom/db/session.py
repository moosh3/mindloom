from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from mindloom.core.config import settings

# Create the SQLAlchemy asynchronous engine
# The engine manages the connection pool.
# Default pool class is QueuePool. We can customize pool_size, max_overflow etc. if needed.
engine = create_async_engine(
    settings.DATABASE_URL.unicode_string(), 
    poolclass=NullPool
    # pool_size=5,  # Default is 5 - Not applicable for NullPool
    # max_overflow=10 # Default is 10 - Not applicable for NullPool
    # echo=True # Uncomment for debugging SQL queries
)

# Create an asynchronous session maker
# expire_on_commit=False prevents attributes from being expired after commit,
# which is useful in async contexts.
async_session_maker = async_sessionmaker(
    bind=engine, 
    expire_on_commit=False, 
    class_=AsyncSession
)

async def get_async_db_session() -> AsyncSession:
    """Dependency function that yields an async session."""
    async with async_session_maker() as session:
        try:
            yield session
            # Optional: If you want commit to happen automatically at the end
            # await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() # Ensure session is closed
