from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from mindloom.db.base_class import Base

# Association Table for Many-to-Many User-Team relationship
team_user_association = Table(
    "team_user_association",
    Base.metadata,
    Column("team_id", UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)

# Add other association tables here if needed in the future
