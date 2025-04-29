from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Schema for the access token response."""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None # Added refresh token

class TokenPayload(BaseModel):
    """Schema for the data encoded within the JWT token."""
    sub: Optional[str] = None # Subject (usually user ID or email)

# Schema for requesting a new access token using a refresh token
class RefreshTokenRequest(BaseModel):
    refresh_token: str
