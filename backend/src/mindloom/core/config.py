import os
import secrets
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Base Path
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")

    # Database
    # Example: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: Optional[PostgresDsn] = Field(None, env="DATABASE_URL")

    # JWT Settings
    # Generate a default secret key for development, ensure it's overridden in production
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 7, env="REFRESH_TOKEN_EXPIRE_MINUTES")

    # AWS S3 Configuration (Optional, only needed if S3 features are used)
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: Optional[str] = Field(None, env="AWS_REGION")
    S3_BUCKET_NAME: Optional[str] = Field(None, env="S3_BUCKET_NAME")

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
