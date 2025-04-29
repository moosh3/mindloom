from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from enum import Enum
from croniter import croniter

class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class ToolConfig(BaseModel):
    name: str = Field(..., description="The name of the tool to use")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional configuration parameters for the tool")

class AgentBase(BaseModel):
    """Base model for Agent properties."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent's purpose")
    instructions: Optional[str] = Field(None, description="Detailed instructions or system prompt for the agent")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="JSON configuration for the language model (e.g., model_id, provider, temperature, api_key_env_var)")
    tools: Optional[List[ToolConfig]] = Field(None, description="List of tools the agent can use, with optional configurations")
    knowledge_config: Optional[Dict[str, Any]] = Field(None, description="JSON configuration for the knowledge base/RAG setup")
    storage_config: Optional[Dict[str, Any]] = Field(None, description="Optional JSON configuration for agent-level storage/memory")
    agent_config: Optional[Dict[str, Any]] = Field(None, description="Additional JSON configuration for Agno Agent parameters")
    content_bucket_ids: Optional[List[uuid.UUID]] = Field(None, description="List of content bucket IDs linked to this agent")
    owner_id: Optional[uuid.UUID] = Field(None, description="ID of the user who owns the agent")

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError('name cannot be empty or just whitespace')
            return stripped
        return v

    @validator('llm_config')
    def llm_config_must_contain_required_keys(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('llm_config must be a dictionary')
            required_keys = {'provider', 'model_id'}
            missing_keys = required_keys - v.keys()
            if missing_keys:
                raise ValueError(f'llm_config is missing required keys: {missing_keys}')
        return v

    class Config:
        extra = "allow"
        from_attributes = True

class AgentCreate(AgentBase):
    """Model for creating a new agent (input)."""
    pass

class AgentUpdate(AgentBase):
    """Model for updating an existing agent (input)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the agent")
    description: Optional[str] = None
    instructions: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[ToolConfig]] = None
    knowledge_config: Optional[Dict[str, Any]] = None
    storage_config: Optional[Dict[str, Any]] = None
    agent_config: Optional[Dict[str, Any]] = None
    content_bucket_ids: Optional[List[uuid.UUID]] = None
    owner_id: Optional[uuid.UUID] = None

    class Config:
        extra = "allow"
        from_attributes = True

class Agent(AgentBase):
    """Model for representing an agent (output), including its ID."""
    id: uuid.UUID = Field(..., description="Unique ID of the agent")
    created_at: datetime
    updated_at: Optional[datetime] = None
    # content_buckets: Optional[List['ContentBucket']] = [] # Requires ContentBucket schema import

    class Config:
        from_attributes = True

# --- SQLAlchemy ORM Model --- #

from sqlalchemy import Column, String, Text, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column, foreign
from sqlalchemy import and_
from mindloom.db.base_class import Base
from mindloom.db.association_tables import team_agent_association
from mindloom.app.models.agent_content_bucket import agent_content_bucket_association
from mindloom.app.models.user import UserORM
from mindloom.app.models.run import RunORM


class AgentORM(Base):
    """Database model for agents."""
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    llm_config: Mapped[dict | None] = mapped_column(JSON)
    tools: Mapped[list[dict] | None] = mapped_column(JSON)
    knowledge_config: Mapped[dict | None] = mapped_column(JSON)
    storage_config: Mapped[dict | None] = mapped_column(JSON)
    agent_config: Mapped[dict | None] = mapped_column(JSON)

    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    owner = relationship(UserORM, back_populates="agents", lazy="selectin")

    runs = relationship(
        RunORM, 
        primaryjoin=lambda: and_(
            foreign(RunORM.runnable_id) == AgentORM.id,
            RunORM.runnable_type == 'agent'
        ),
        backref="agent", 
        cascade="all, delete-orphan",
        lazy="selectin",
        overlaps="team,runs"
    )
    schedules = relationship("AgentScheduleORM", back_populates="agent", cascade="all, delete-orphan")
    variables = relationship("AgentVariableORM", back_populates="agent", cascade="all, delete-orphan", lazy="selectin")
    teams = relationship(
        "TeamORM",
        secondary=team_agent_association,
        back_populates="agents",
        lazy="selectin"
    )
    content_buckets = relationship(
        "ContentBucketORM",
        secondary=agent_content_bucket_association,
        back_populates="agents",
        lazy="selectin"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}')>"

# --- Agent Schedule Models --- #

class AgentScheduleBase(BaseModel):
    """Base model for Agent Schedule properties."""
    agent_id: uuid.UUID = Field(..., description="ID of the agent being scheduled")
    cron_schedule: str = Field(..., description="Cron expression for the schedule (e.g., '0 9 * * 1-5')")
    input_variables: Optional[Dict[str, Any]] = Field(None, description="Default input variables for scheduled runs")
    is_enabled: bool = Field(True, description="Whether the schedule is currently active")

    @validator('cron_schedule')
    def validate_cron_schedule(cls, v):
        try:
            croniter(v)
        except ValueError as e:
            raise ValueError(f"Invalid cron expression: {e}")
        return v

    class Config:
        extra = "allow"
        from_attributes = True

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

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), index=True)

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

    @validator('key')
    def key_must_not_be_empty(cls, v):
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError('key cannot be empty or just whitespace')
            # Optional: Check for invalid characters if needed
            return stripped # Return the stripped key
        return v

    class Config:
        extra = "allow"
        from_attributes = True

class AgentVariableCreate(AgentVariableBase):
    """Model for creating a new agent variable."""
    pass

class AgentVariableUpdate(BaseModel):
    """Model for updating an agent variable. Only value and description can be updated."""
    value: Optional[Any] = None
    description: Optional[str] = None
    is_secret: Optional[bool] = None

class AgentVariable(AgentVariableBase):
    """Model for representing an agent variable, including its ID."""
    id: uuid.UUID = Field(..., description="Unique identifier for the variable")
    created_at: datetime = Field(..., description="Timestamp when the variable was created")
    updated_at: datetime = Field(..., description="Timestamp when the variable was last updated")

    class Config:
        from_attributes = True

# --- SQLAlchemy ORM Model for Agent Variable --- #

from sqlalchemy import UniqueConstraint

class AgentVariableORM(Base):
    """Database model for agent variables."""
    __tablename__ = "agent_variables"
    __table_args__ = (UniqueConstraint('agent_id', 'key', name='uq_agent_variable_key'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)

    agent = relationship("AgentORM", back_populates="variables")

    def __repr__(self):
        secret_marker = " (secret)" if self.is_secret else ""
        return f"<AgentVariable(id={self.id}, agent_id={self.agent_id}, key='{self.key}'{secret_marker})>"
