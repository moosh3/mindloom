from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models in the application."""
    # You can define common attributes or methods for all models here if needed
    # Example: Define a default __tablename__ generation
    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return cls.__name__.lower() + "s" # Simple pluralization
    pass
