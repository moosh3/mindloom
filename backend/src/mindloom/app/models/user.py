import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from mindloom.db.base_class import Base
from mindloom.db.association_tables import team_user_association

class User(Base):
    """Database model for users."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))
    # department: Mapped[str | None] = mapped_column(String(100)) # Add later if needed

    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean(), default=False)
    # role: Mapped[str] = mapped_column(String(50), default="user") # Add later for RBAC

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    agents = relationship("AgentORM", back_populates="owner", cascade="all, delete-orphan")
    teams = relationship(
        "TeamORM",
        secondary=team_user_association,
        back_populates="members", 
        lazy="selectin"
    )
    runs = relationship("RunORM", back_populates="user", cascade="all, delete-orphan") # Relationship to runs initiated by user

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
