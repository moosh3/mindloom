from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from mindloom.app.models.user import User, UserCreate, UserORM
from mindloom.app.models.token import Token, RefreshTokenRequest
from mindloom.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_refresh_token
from mindloom.dependencies import get_db, get_current_user
import uuid

router = APIRouter()

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Register a new user."""
    # Check if user already exists
    statement = select(UserORM).where(UserORM.email == user_in.email)
    result = await db.execute(statement)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash the password
    hashed_password = get_password_hash(user_in.password)

    # Create new user ORM instance
    # Note: Exclude password from the model_dump when creating ORM object
    user_data = user_in.model_dump(exclude={"password"})
    db_user = UserORM(**user_data, hashed_password=hashed_password)

    # Add user to DB
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Return the created user data (using the User schema, which excludes password)
    return User.from_orm(db_user) # Use Pydantic v2 method

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Authenticate user and return an access token."""
    # Find user by email
    statement = select(UserORM).where(UserORM.email == form_data.username) # OAuth form uses 'username' field for email
    result = await db.execute(statement)
    user = result.scalars().first()

    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard for unauthorized responses
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Generate access token (Subject is the user's ID)
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id) # Generate refresh token
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token) # Return both tokens

@router.post("/refresh", response_model=Token, tags=["Auth"])
async def refresh_access_token(
    request_body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Refresh the access token using a valid refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    refresh_token = request_body.refresh_token
    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
        
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # Optional: Check if user still exists in DB (good practice)
    user = await db.get(UserORM, user_id)
    if user is None:
        raise credentials_exception

    # Create a new access token
    new_access_token = create_access_token(subject=user_id)
    # Note: We only return the new access token here.
    # The refresh token remains the same until it expires or is revoked.
    return Token(access_token=new_access_token, token_type="bearer")

@router.get("/users/me", response_model=User, tags=["Auth"])
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> User:
    """Fetch the current logged-in user's details."""
    # The get_current_user dependency already handles fetching and validating the user
    return current_user
