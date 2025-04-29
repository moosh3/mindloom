import uuid
from datetime import datetime
from typing import Optional, Set

from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from mindloom.db.base_class import Base
from mindloom.db.association_tables import team_user_association

# SQLAlchemy ORM Model
class UserORM(Base):
    """Database model for users."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100)) # Added department

    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean(), default=False)
    role: Mapped[str] = mapped_column(String(50), default="user") # Added for RBAC

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relationships (Ensure related models refer to UserORM if needed)
    agents = relationship("AgentORM", back_populates="owner", cascade="all, delete-orphan")
    teams = relationship(
        "TeamORM",
        secondary=team_user_association,
        back_populates="members",
        lazy="selectin"
    )
    runs = relationship("RunORM", back_populates="user", cascade="all, delete-orphan") # Relationship to runs initiated by user

    def __repr__(self):
        return f"<UserORM(id={self.id}, email='{self.email}')>"

# Pydantic Models (Schemas)

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100) # Added department
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    role: str = "user" # Added role

    _allowed_roles: Set[str] = {"user", "admin"} # Define allowed roles

    @validator('full_name', 'department')
    def field_must_not_be_empty_or_whitespace(cls, v):
        if v is not None:
            if isinstance(v, str):
                stripped = v.strip()
                if not stripped:
                    raise ValueError('Field cannot be empty or just whitespace')
                # Optional: Add min_length check here if needed, e.g., len(stripped) >= 1
                return stripped # Return stripped value
            else:
                # Handle non-string case if necessary, or raise error
                raise ValueError('Field must be a string')
        return v

    @validator('role')
    def role_must_be_allowed(cls, v):
        if v not in cls._allowed_roles:
            raise ValueError(f"Invalid role '{v}'. Allowed roles are: {cls._allowed_roles}")
        return v

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# Properties to receive via API on update (Not used yet, but good practice)
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8)

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Replaces orm_mode = True

# Properties to return to client
class User(UserInDBBase):
    pass

# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
