from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Set
import uuid
from datetime import datetime

class TeamBase(BaseModel):
    """Base model for Team properties."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the team")
    description: Optional[str] = Field(None, description="Description of the team's purpose")
    mode: Optional[List[str]] = Field(None, description="Agno team execution mode(s) (e.g., ['coordinate', 'collaborate'])")
    instructions: Optional[str] = Field(None, description="Instructions for the team leader/operation")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="JSON configuration for the team leader's language model")
    knowledge_config: Optional[Dict[str, Any]] = Field(None, description="Optional JSON configuration for team-level knowledge base")
    storage_config: Optional[Dict[str, Any]] = Field(None, description="Optional JSON configuration for team-level storage/memory")
    team_config: Optional[Dict[str, Any]] = Field(None, description="Additional JSON configuration for Agno Team parameters")
    enable_memory: bool = Field(False, description="Enable conversation history memory for the team")
    history_length: int = Field(5, description="Number of past interactions to include in history", ge=1)
    agent_ids: List[uuid.UUID] = Field(default_factory=list, description="List of agent IDs belonging to the team")

    _allowed_modes: Set[str] = {"coordinate", "collaborate"}

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError('name cannot be empty or just whitespace')
            return stripped
        return v

    @validator('description', 'instructions')
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @validator('mode')
    def mode_must_be_allowed(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("'mode' must be a list of strings")
            invalid_modes = set(v) - cls._allowed_modes
            if invalid_modes:
                raise ValueError(f"Invalid mode(s) found: {invalid_modes}. Allowed modes: {cls._allowed_modes}")
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

class TeamCreate(TeamBase):
    """Model for creating a new team (input)."""
    agent_ids: Optional[List[uuid.UUID]] = Field(None, description="List of initial agent IDs to add to the team")
    enable_memory: Optional[bool] = None
    history_length: Optional[int] = Field(None, ge=1)

class TeamUpdate(BaseModel):
    """Model for updating an existing team (input)."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    mode: Optional[List[str]] = None
    instructions: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    knowledge_config: Optional[Dict[str, Any]] = None
    storage_config: Optional[Dict[str, Any]] = None
    team_config: Optional[Dict[str, Any]] = None
    enable_memory: Optional[bool] = None
    history_length: Optional[int] = Field(None, ge=1)
    agent_ids: Optional[List[uuid.UUID]] = None

class Team(TeamBase):
    """Model for representing a team (output), including its ID."""
    id: uuid.UUID = Field(..., description="Unique identifier for the team")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# --- Pydantic Schemas for Run Endpoint --- #

class TeamRunInput(BaseModel):
    input: str = Field(..., min_length=1, description="The input query or task for the team to process.")

    @validator('input')
    def input_must_not_be_empty(cls, v):
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError('input cannot be empty or just whitespace')
            return stripped
        return v

class TeamRunOutput(BaseModel):
    output: Any = Field(..., description="The result from the Agno team execution.")

# --- SQLAlchemy ORM Model --- #

from sqlalchemy import Column, String, Text, Table, ForeignKey, DateTime, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from mindloom.db.base_class import Base
from mindloom.db.association_tables import team_user_association, team_agent_association

class TeamORM(Base):
    """Database model for teams."""
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[list[str] | None] = mapped_column(JSON)
    instructions: Mapped[str | None] = mapped_column(Text)
    llm_config: Mapped[dict | None] = mapped_column(JSON)
    knowledge_config: Mapped[dict | None] = mapped_column(JSON)
    storage_config: Mapped[dict | None] = mapped_column(JSON)
    team_config: Mapped[dict | None] = mapped_column(JSON)
    enable_memory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    history_length: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relationship: Many-to-Many with Users (Team Members)
    members = relationship(
        "User",
        secondary=team_user_association,
        back_populates="teams", # Define 'teams' relationship in User model
        lazy="selectin"
    )

    # Relationship: Many-to-Many with Agents
    agents = relationship(
        "AgentORM",
        secondary=team_agent_association,
        back_populates="teams", # Define 'teams' relationship in AgentORM model
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"
