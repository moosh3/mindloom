from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from mindloom.db.base_class import Base

team_content_bucket_association = Table(
    "team_content_bucket_association",
    Base.metadata,
    Column("team_id", UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
    Column("content_bucket_id", UUID(as_uuid=True), ForeignKey("content_buckets.id", ondelete="CASCADE"), primary_key=True),
)
