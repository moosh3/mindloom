from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from mindloom.core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The subject of the token (usually user ID).
        expires_delta: Optional timedelta for expiration. Defaults to configured refresh token expiry.

    Returns:
        The encoded JWT refresh token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "token_type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes a JWT access token, returning the payload or None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Add basic validation (e.g., check if 'sub' exists)
        if 'sub' not in payload or 'token_type' not in payload:
            return None
        # Optionally, check token_type for access token explicitly if needed
        # if payload.get("token_type") != "access":
        #     return None
        return payload
    except jwt.ExpiredSignatureError:
        # Handle expired token specifically if needed
        return None
    except jwt.PyJWTError:
        return None

def decode_refresh_token(token: str) -> Optional[dict]:
    """Decodes a JWT refresh token, returning the payload or None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Validate essential claims and token type
        if 'sub' not in payload or payload.get("token_type") != "refresh":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        # Handle expired token specifically if needed
        return None
    except jwt.PyJWTError:
        return None
