from fastapi import FastAPI
from mindloom.app.api.v1.api import api_router as api_v1_router
from mindloom.app.middleware.error_handling import CustomErrorHandlerMiddleware
import logging
import asyncio
import os
import sys
from contextlib import asynccontextmanager

# External dependencies for connectivity checks
import boto3
from sqlalchemy import text
from botocore.exceptions import ClientError, BotoCoreError

# Internal modules
from mindloom.core.config import settings
from mindloom.db.session import engine
from mindloom.services.redis import initialize_async as init_redis, close as close_redis

# Configure logging basic setup FIRST
logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(name)s: %(message)s')

# Configure module-level logger AFTER basicConfig
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan Management
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("--- Application Starting Up --- ")
    # Startup Sequence -------------------------------------------------------
    # 1. Database check ------------------------------------------------------
    logger.info("Performing database connectivity check …")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connectivity check passed")
    except Exception as exc:
        logger.error("Database connectivity check failed: %s", exc)
        raise RuntimeError("Database connectivity check failed") from exc

    # 2. Redis check ---------------------------------------------------------
    logger.info("Performing Redis connectivity check …")
    try:
        await init_redis()
        logger.info("Redis connectivity check passed")
    except Exception as exc:
        logger.error("Redis connectivity check failed: %s", exc)
        raise RuntimeError("Redis connectivity check failed") from exc

    # 3. S3 / MinIO check ----------------------------------------------------
    logger.info("Performing S3 connectivity check …")
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION or "us-east-1",
        )

        def _check_bucket() -> None:
            """Run synchronous boto3 call in a thread."""
            if settings.S3_BUCKET_NAME:
                # Check if bucket exists / is accessible
                s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            else:
                # Fall back to a simple list operation
                s3_client.list_buckets()

        await asyncio.to_thread(_check_bucket)
        logger.info("S3 connectivity check passed")
    except (ClientError, BotoCoreError, Exception) as exc:
        logger.error("S3 connectivity check failed: %s", exc)
        raise RuntimeError("S3 connectivity check failed") from exc

    # 4. Alembic Migrations check --------------------------------------------
    logger.info("Running Alembic migrations …")
    try:
        alembic_cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini"))
        logger.debug(f"Using Alembic config path: {alembic_cfg_path}")
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m", "alembic",
            "-c", alembic_cfg_path,
            "upgrade", "head",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logger.error(f"Alembic migration failed. Return code: {process.returncode}")
            logger.error(f"Stderr: {stderr.decode().strip()}")
            raise RuntimeError("Alembic migration failed")
        else:
            logger.info("Alembic migrations applied successfully or are up-to-date.")
            if stdout:
                logger.info(f"Stdout: {stdout.decode().strip()}")
            if stderr:
                 logger.warning(f"Stderr: {stderr.decode().strip()}")
    except FileNotFoundError:
        logger.error(f"Alembic configuration file not found at {alembic_cfg_path}")
        raise RuntimeError("Alembic configuration file not found.")
    except Exception as exc:
        logger.error(f"An error occurred during Alembic migrations: {exc}")
        raise RuntimeError("Alembic migration check failed") from exc

    logger.info("--- Startup Checks Completed --- ")
    yield # Application runs after this point
    # Shutdown Sequence ------------------------------------------------------
    logger.info("--- Application Shutting Down --- ")
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as exc:
        logger.warning("Failed to close Redis connection gracefully: %s", exc)
    logger.info("--- Shutdown Cleanup Completed --- ")


app = FastAPI(
    title="Mindloom API",
    version="0.1.0",
    description="API for managing Mindloom Agents, Teams, and Runs.",
    lifespan=lifespan # Register the lifespan context manager
)

# Add the custom error handling middleware
app.add_middleware(CustomErrorHandlerMiddleware)

@app.get("/health", tags=["Health"])
async def health_check():
    """Check the health of the API."""
    return {"status": "ok"}

# Include the v1 API router
app.include_router(api_v1_router, prefix="/api/v1")

# Placeholder for future API routers
# from app.api.v1 import api_router
# app.include_router(api_router, prefix="/api/v1")
