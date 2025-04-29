from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from mindloom.db.base_class import Base

agent_content_bucket_association = Table(
    "agent_content_bucket_association",
    Base.metadata,
    Column("agent_id", UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("content_bucket_id", UUID(as_uuid=True), ForeignKey("content_buckets.id", ondelete="CASCADE"), primary_key=True),
)
