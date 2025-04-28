from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

class TeamBase(BaseModel):
    """Base model for Team properties."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the team")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the team")
    # For now, just store agent IDs. Later, this might involve relationships.
    agent_ids: List[uuid.UUID] = Field(default_factory=list, description="List of agent IDs belonging to the team")
    # team_type: Optional[str] = Field(None, description="Type of team (e.g., 'Route', 'Coordinate', 'Collaborate')") # Add later if needed

class TeamCreate(TeamBase):
    """Model for creating a new team (input)."""
    pass

class TeamUpdate(TeamBase):
    """Model for updating an existing team (input)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    agent_ids: Optional[List[uuid.UUID]] = None

class Team(TeamBase):
    """Model for representing a team (output), including its ID."""
    id: uuid.UUID = Field(..., description="Unique identifier for the team")

    class Config:
        from_attributes = True # Pydantic v2 uses this instead of orm_mode

# --- SQLAlchemy ORM Model --- #

from sqlalchemy import Column, String, Text, Table, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from mindloom.db.base_class import Base
from mindloom.db.association_tables import team_user_association, team_agent_association

class TeamORM(Base):
    """Database model for teams."""
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
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
