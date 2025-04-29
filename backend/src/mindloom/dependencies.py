from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from mindloom.db.session import async_session_maker

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mindloom.app.models.token import TokenPayload
from mindloom.app.models.user import User, UserORM
from mindloom.core import security
from mindloom.core.config import settings

# OAuth2 scheme: expects token in 'Authorization: Bearer <token>' header
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login" # Points to the login endpoint
)

logger = logging.getLogger(__name__)

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

# --- Service Dependencies --- #

from mindloom.services.agents import AgentService
from mindloom.services.teams import TeamService

def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    """Dependency provider for AgentService."""
    return AgentService(db=db)

def get_team_service(
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service)
) -> TeamService:
    """Dependency provider for TeamService, requires AgentService."""
    return TeamService(db=db, agent_service=agent_service)

# --- Authentication Dependencies --- #

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """Decode JWT token and return the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError) as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception

    # Fetch user from DB based on token subject (user ID)
    statement = select(UserORM).where(UserORM.id == token_data.sub)
    result = await db.execute(statement)
    user = result.scalars().first()

    if user is None:
        logger.warning(f"User not found for token sub: {token_data.sub}")
        raise credentials_exception

    # Check if user is active (can add other checks later)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return User.from_orm(user) # Return Pydantic User model

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if the current user is an active superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    # User is already verified as active by get_current_user
    return current_user
