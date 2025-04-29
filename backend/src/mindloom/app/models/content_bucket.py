import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field

from mindloom.db.base_class import Base
# Import association tables
from mindloom.app.models.agent_content_bucket import agent_content_bucket_association
from mindloom.app.models.team_content_bucket import team_content_bucket_association

# Forward reference for relationship type hinting (use strings in relationship definitions)
# from mindloom.app.models.file_metadata import FileMetadataORM
# from mindloom.app.models.agent import AgentORM
# from mindloom.app.models.team import TeamORM

# --- Pydantic Schemas ---

class ContentBucketBase(BaseModel):
    name: str = Field(..., max_length=100, description="Name of the content bucket")
    description: Optional[str] = Field(None, description="Description of the content bucket")
    bucket_type: str = Field(..., description="Type of the bucket source (e.g., 'S3', 'Local', 'URL')")
    config: Dict[str, Any] = Field(..., description="Configuration specific to the bucket_type (e.g., bucket name, path)")
    embedder_config: Dict[str, Any] = Field(..., description="Configuration for the embedder model")
    vector_db_config: Dict[str, Any] = Field(..., description="Configuration for the vector database")
    # user_id: Optional[uuid.UUID] = Field(None, description="User who owns this bucket") # Add if needed

class ContentBucketCreate(ContentBucketBase):
    pass

class ContentBucketUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    bucket_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    embedder_config: Optional[Dict[str, Any]] = None
    vector_db_config: Optional[Dict[str, Any]] = None

class ContentBucket(ContentBucketBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    # files: List['FileMetadata'] = [] # Add if FileMetadata schema is defined and needed here
    # agents: List['Agent'] = [] # Add if Agent schema is defined and needed here

    class Config:
        from_attributes = True

# --- SQLAlchemy ORM Model ---

class ContentBucketORM(Base):
    __tablename__ = "content_buckets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    bucket_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    embedder_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    vector_db_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id")) # Add relationship if needed

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relationship: One-to-Many with Files
    files = relationship("FileMetadataORM", back_populates="bucket", cascade="all, delete-orphan", lazy="selectin")

    # Relationship: Many-to-Many with Agents
    agents = relationship(
        "AgentORM",
        secondary=agent_content_bucket_association, # Use imported table object
        back_populates="content_buckets",
        lazy="selectin"
    )

    # Relationship: Many-to-Many with Teams
    teams = relationship(
        "TeamORM",
        secondary=team_content_bucket_association, # Use imported table object
        back_populates="content_buckets",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<ContentBucket(id={self.id}, name='{self.name}', type='{self.bucket_type}')>"
