from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

class AgentBase(BaseModel):
    """Base model for Agent properties."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the agent")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the agent")
    model_provider: str = Field(..., description="LLM provider (e.g., 'azure', 'openai')")
    model_name: str = Field(..., description="Specific model name (e.g., 'gpt-4', 'gpt-3.5-turbo')")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Model temperature setting")
    # Placeholder for more complex fields
    tools: List[str] = Field(default_factory=list, description="List of tools the agent can use")
    # content_bucket_ids: List[uuid.UUID] = Field(default_factory=list)

class AgentCreate(AgentBase):
    """Model for creating a new agent (input)."""
    pass

class AgentUpdate(AgentBase):
    """Model for updating an existing agent (input)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    tools: Optional[List[str]] = None

class Agent(AgentBase):
    """Model for representing an agent (output), including its ID."""
    id: uuid.UUID = Field(..., description="Unique identifier for the agent")

    class Config:
        from_attributes = True # Pydantic v2 uses this instead of orm_mode

# --- SQLAlchemy ORM Model --- #

from sqlalchemy import Column, String, Float, ForeignKey, Text, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from mindloom.db.base_class import Base
from mindloom.db.association_tables import team_agent_association # Import association table

class AgentORM(Base):
    """Database model for agents."""
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    tools: Mapped[list[str] | None] = mapped_column(JSON) # Store list of tools as JSON

    # Foreign Key to User table
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationship (optional, useful for ORM access)
    owner = relationship("User", back_populates="agents", lazy="selectin") # Adjust back_populates later if needed

    # Relationships to other potential models (e.g., Runs, ContentBuckets)
    runs = relationship("RunORM", back_populates="agent", cascade="all, delete-orphan") # Relationship to runs performed by this agent
    schedules = relationship("AgentScheduleORM", back_populates="agent", cascade="all, delete-orphan")
    variables = relationship("AgentVariableORM", back_populates="agent", cascade="all, delete-orphan", lazy="selectin")
    # Relationship: Many-to-Many with Teams
    teams = relationship(
        "TeamORM",
        secondary=team_agent_association,
        back_populates="agents", # Corresponds to 'agents' in TeamORM
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}')>"

# Add back-population to User model if needed
# In user.py:
# agents = relationship("Agent", back_populates="owner")


# --- Agent Schedule Models --- #

class AgentScheduleBase(BaseModel):
    """Base model for Agent Schedule properties."""
    agent_id: uuid.UUID = Field(..., description="ID of the agent being scheduled")
    cron_schedule: str = Field(..., description="Cron expression for the schedule (e.g., '0 9 * * 1-5')")
    input_variables: Optional[Dict[str, Any]] = Field(None, description="Default input variables for scheduled runs")
    is_enabled: bool = Field(True, description="Whether the schedule is currently active")

class AgentScheduleCreate(AgentScheduleBase):
    """Model for creating a new agent schedule."""
    pass

class AgentScheduleUpdate(BaseModel):
    """Model for updating an agent schedule."""
    cron_schedule: Optional[str] = None
    input_variables: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None

class AgentSchedule(AgentScheduleBase):
    """Model for representing an agent schedule, including its ID."""
    id: uuid.UUID = Field(..., description="Unique identifier for the schedule")
    created_at: datetime = Field(..., description="Timestamp when the schedule was created")
    updated_at: datetime = Field(..., description="Timestamp when the schedule was last updated")
    last_run_at: Optional[datetime] = Field(None, description="Timestamp of the last run triggered by this schedule")

    class Config:
        from_attributes = True

# --- SQLAlchemy ORM Model for Agent Schedule --- #

class AgentScheduleORM(Base):
    """Database model for agent schedules."""
    __tablename__ = "agent_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cron_schedule: Mapped[str] = mapped_column(String, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    input_variables: Mapped[dict | None] = mapped_column(JSON)

    # Foreign Key to Agent
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), index=True)

    # Relationship to Agent
    agent = relationship("AgentORM", back_populates="schedules", lazy="selectin")

    def __repr__(self):
        return f"<AgentSchedule(id={self.id}, agent_id={self.agent_id}, schedule='{self.cron_schedule}')>"


# --- Agent Variable Models --- #

class AgentVariableBase(BaseModel):
    """Base model for Agent Variable properties."""
    agent_id: uuid.UUID = Field(..., description="ID of the agent this variable belongs to")
    key: str = Field(..., min_length=1, max_length=100, description="Variable key (name)")
    value: Any = Field(..., description="Variable value (can be any JSON-serializable type)")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the variable")
    is_secret: bool = Field(False, description="Whether this variable should be treated as a secret")

class AgentVariableCreate(AgentVariableBase):
    """Model for creating a new agent variable."""
    pass

class AgentVariableUpdate(BaseModel):
    """Model for updating an agent variable. Only value and description can be updated."""
    value: Optional[Any] = None
    description: Optional[str] = None
    is_secret: Optional[bool] = None # Allow updating secrecy flag

class AgentVariable(AgentVariableBase):
    """Model for representing an agent variable, including its ID."""
    id: uuid.UUID = Field(..., description="Unique identifier for the variable")
    created_at: datetime = Field(..., description="Timestamp when the variable was created")
    updated_at: datetime = Field(..., description="Timestamp when the variable was last updated")

    class Config:
        from_attributes = True

# --- SQLAlchemy ORM Model for Agent Variable --- #

from sqlalchemy import UniqueConstraint # Import UniqueConstraint

class AgentVariableORM(Base):
    """Database model for agent variables."""
    __tablename__ = "agent_variables"
    __table_args__ = (UniqueConstraint('agent_id', 'key', name='uq_agent_variable_key'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Store potentially sensitive values in a way that can be encrypted/decrypted later if needed
    # For now, using JSON, but consider specific encryption field types if security demands it
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign Key to Agent
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)

    # Relationship to Agent
    agent = relationship("AgentORM", back_populates="variables")

    def __repr__(self):
        secret_marker = " (secret)" if self.is_secret else ""
        return f"<AgentVariable(id={self.id}, agent_id={self.agent_id}, key='{self.key}'{secret_marker})>"
