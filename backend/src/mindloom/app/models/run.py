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
from mindloom.app.models.user import UserORM

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

    # Store runnable details directly
    runnable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    runnable_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # 'agent' or 'team'

    # Foreign Keys
    # A run is typically initiated by a User (optional if system-initiated)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    user = relationship(UserORM, back_populates="runs", lazy="selectin")
    logs = relationship("RunLogORM", back_populates="run", cascade="all, delete-orphan", lazy="selectin") # Relationship to logs
    artifacts = relationship("RunArtifactORM", back_populates="run", cascade="all, delete-orphan") # Relationship to artifacts

    def __repr__(self):
        return f"<Run(id={self.id}, runnable_id={self.runnable_id}, type='{self.runnable_type}', status='{self.status}')>"

# Add back-population to User model:
# In user.py:
# runs = relationship("RunORM", back_populates="user")


# --- Run Log Models --- #

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class RunLogBase(BaseModel):
    """Base model for Run Log properties."""
    run_id: uuid.UUID = Field(..., description="ID of the run this log belongs to")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the log entry")
    level: LogLevel = Field(LogLevel.INFO, description="Log level (e.g., INFO, ERROR)")
    message: str = Field(..., description="Log message content")
    log_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional structured metadata")

class RunLogCreate(RunLogBase):
    """Model for creating a new run log entry (typically done internally)."""
    pass

class RunLog(RunLogBase):
    """Model for representing a run log entry, including its ID."""
    id: uuid.UUID = Field(..., description="Unique identifier for the log entry")

    class Config:
        from_attributes = True

# --- SQLAlchemy ORM Model for Run Log --- #

from sqlalchemy import Text # Import Text type

class RunLogORM(Base):
    """Database model for run logs."""
    __tablename__ = "run_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    level: Mapped[LogLevel] = mapped_column(SQLAlchemyEnum(LogLevel), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    log_metadata: Mapped[dict | None] = mapped_column(JSON)

    # Foreign Key to Run
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False, index=True)

    # Relationship to Run
    run = relationship("RunORM", back_populates="logs")

    def __repr__(self):
        return f"<RunLog(id={self.id}, run_id={self.run_id}, level='{self.level}')>"


# --- Run Artifact Models --- #

class ArtifactType(str, Enum):
    FILE = "file"
    IMAGE = "image"
    TEXT = "text"
    JSON = "json"
    OTHER = "other"

class RunArtifactBase(BaseModel):
    """Base model for Run Artifact properties."""
    run_id: uuid.UUID = Field(..., description="ID of the run this artifact belongs to")
    name: str = Field(..., description="Name of the artifact (e.g., filename)")
    artifact_type: ArtifactType = Field(ArtifactType.OTHER, description="Type of the artifact")
    # Store location or reference, not the data itself in the DB usually
    storage_path: Optional[str] = Field(None, description="Path or reference to where the artifact is stored (e.g., S3 URL, local path)")
    content_type: Optional[str] = Field(None, description="MIME type of the artifact")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata about the artifact")

class RunArtifactCreate(RunArtifactBase):
    """Model for creating a new run artifact entry (typically done internally)."""
    pass

class RunArtifact(RunArtifactBase):
    """Model for representing a run artifact entry, including its ID."""
    id: uuid.UUID = Field(..., description="Unique identifier for the artifact entry")
    created_at: datetime = Field(..., description="Timestamp when the artifact entry was created")

    class Config:
        from_attributes = True

# --- SQLAlchemy ORM Model for Run Artifact --- #

class RunArtifactORM(Base):
    """Database model for run artifacts."""
    __tablename__ = "run_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(SQLAlchemyEnum(ArtifactType), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024)) # Path/URL reference
    content_type: Mapped[str | None] = mapped_column(String(100))
    artifact_metadata: Mapped[dict | None] = mapped_column(JSON) # Renamed from metadata

    # Foreign Key to Run
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False, index=True)

    # Relationship to Run
    run = relationship("RunORM", back_populates="artifacts")

    def __repr__(self):
        return f"<RunArtifact(id={self.id}, run_id={self.run_id}, name='{self.name}')>"
