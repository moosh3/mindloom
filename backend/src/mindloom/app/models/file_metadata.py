import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field

from mindloom.db.base_class import Base

# --- Pydantic Schemas ---

class FileMetadataBase(BaseModel):
    filename: str = Field(..., description="Original filename")
    s3_bucket: str = Field(..., description="S3(-compatible) bucket name where the file is stored")
    s3_key: str = Field(..., description="S3(-compatible) key (path) for the file")
    content_type: Optional[str] = Field(None, description="MIME type of the file")
    size_bytes: Optional[int] = Field(None, description="Size of the file in bytes")
    # Using last_modified from S3 or upload time might be simpler than reliable hashing initially
    last_modified: datetime = Field(..., description="Last modified timestamp (from S3 or upload time)")
    # content_hash: Optional[str] = Field(None, description="Optional hash (e.g., MD5, SHA256) of the file content")
    bucket_id: uuid.UUID = Field(..., description="ID of the content bucket this file belongs to")

class FileMetadataCreate(FileMetadataBase):
    pass

class FileMetadataUpdate(BaseModel):
    # Usually, metadata isn't updated directly, files are re-uploaded or deleted
    pass

class FileMetadata(FileMetadataBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

# --- SQLAlchemy ORM Model ---

class FileMetadataORM(Base):
    __tablename__ = "file_metadata"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger) # Use BigInteger for potentially large files
    last_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    # content_hash: Mapped[str | None] = mapped_column(String(64)) # e.g., SHA256

    bucket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_buckets.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship: Many-to-One with ContentBucket
    bucket = relationship("ContentBucketORM", back_populates="files")

    def __repr__(self):
        return f"<FileMetadata(id={self.id}, filename='{self.filename}', key='{self.s3_key}')>"
