import os
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    # Example: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: Optional[PostgresDsn] = Field(None, env="DATABASE_URL")

    # Allow loading from .env file if needed (requires python-dotenv)
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Ensure DATABASE_URL is set
if not settings.DATABASE_URL:
    # Attempt to build from individual parts if DATABASE_URL is not set directly
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_server = os.getenv("POSTGRES_SERVER", "db") # 'db' is the service name in docker-compose
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "mindloom_dev")

    settings.DATABASE_URL = PostgresDsn(
        f"postgresql+asyncpg://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}"
    )

print(f"Using Database URL: {settings.DATABASE_URL.unicode_string()}") # For debugging during startup
