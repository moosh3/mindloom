from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid

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

from sqlalchemy import Column, String, Float, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from mindloom.db.base_class import Base

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

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}')>"

# Add back-population to User model if needed
# In user.py:
# agents = relationship("Agent", back_populates="owner")
