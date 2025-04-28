from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import uuid
from datetime import datetime
from enum import Enum

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RunBase(BaseModel):
    """Base model for Run properties."""
    # Reference to the entity being run (can be Agent or Team)
    # Using Union requires careful handling later, especially with DB relationships
    runnable_id: uuid.UUID = Field(..., description="ID of the Agent or Team being run")
    runnable_type: str = Field(..., description="Type of runnable ('agent' or 'team')") # To distinguish between Agent/Team IDs
    input_variables: Optional[Dict[str, Any]] = Field(None, description="Input variables for the run")

class RunCreate(RunBase):
    """Model for creating/starting a new run (input)."""
    pass

# Note: We likely won't update a run directly via PUT, but maybe change its status (e.g., cancel)
# class RunUpdate(BaseModel):
#     status: Optional[RunStatus] = None

class Run(RunBase):
    """Model for representing a run (output), including its ID and status."""
    id: uuid.UUID = Field(..., description="Unique identifier for the run")
    status: RunStatus = Field(RunStatus.PENDING, description="Current status of the run")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the run was created")
    started_at: Optional[datetime] = Field(None, description="Timestamp when the run started execution")
    ended_at: Optional[datetime] = Field(None, description="Timestamp when the run finished (completed, failed, or cancelled)")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output data or results from the run")
    # logs: Optional[List[str]] = Field(None) # Add later for logs/artifacts
    # artifacts: Optional[List[str]] = Field(None)

    class Config:
        from_attributes = True

# --- SQLAlchemy ORM Model --- #

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from mindloom.db.base_class import Base
# We need AgentORM and User for relationships
# Ensure AgentORM exists in agent.py
# Ensure User exists in user.py

class RunORM(Base):
    """Database model for runs."""
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[RunStatus] = mapped_column(SQLAlchemyEnum(RunStatus), nullable=False, default=RunStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    input_variables: Mapped[dict | None] = mapped_column(JSON)
    output_data: Mapped[dict | None] = mapped_column(JSON)

    # Foreign Keys
    # A run is typically initiated by a User (optional if system-initiated)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    # A run is executed by an Agent
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))

    # Relationships
    user = relationship("User", back_populates="runs", lazy="selectin")
    agent = relationship("AgentORM", back_populates="runs", lazy="selectin")

    def __repr__(self):
        return f"<Run(id={self.id}, agent_id={self.agent_id}, status='{self.status}')>"

# Add back-population to User model:
# In user.py:
# runs = relationship("RunORM", back_populates="user")

# Add back-population to AgentORM model:
# In agent.py:
# runs = relationship("RunORM", back_populates="agent")
