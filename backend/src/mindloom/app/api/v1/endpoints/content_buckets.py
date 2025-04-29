import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mindloom.dependencies import get_db, get_current_user
from mindloom.app.models.content_bucket import (
    ContentBucket,
    ContentBucketCreate,
    ContentBucketUpdate,
)
from mindloom.services.content_buckets import ContentBucketService
from mindloom.services.exceptions import ServiceError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/content_buckets",
    tags=["Content Buckets"],
    dependencies=[Depends(get_current_user)] # Require authentication
)

# Dependency to get the service
def get_content_bucket_service(db: AsyncSession = Depends(get_db)) -> ContentBucketService:
    return ContentBucketService(db)


@router.post("/", response_model=ContentBucket, status_code=status.HTTP_201_CREATED)
async def create_content_bucket(
    bucket_in: ContentBucketCreate,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> ContentBucket:
    """Create a new content bucket configuration."""
    try:
        db_bucket = await service.create_bucket(bucket_in)
        return ContentBucket.from_orm(db_bucket)
    except ServiceError as e:
        logger.error(f"API Error creating content bucket: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected API error creating content bucket: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get("/", response_model=List[ContentBucket])
async def read_content_buckets(
    skip: int = 0,
    limit: int = 100,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> List[ContentBucket]:
    """Retrieve a list of content bucket configurations."""
    try:
        db_buckets = await service.get_buckets(skip=skip, limit=limit)
        return [ContentBucket.from_orm(bucket) for bucket in db_buckets]
    except Exception as e:
        logger.exception(f"Unexpected API error reading content buckets: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get("/{bucket_id}", response_model=ContentBucket)
async def read_content_bucket(
    bucket_id: uuid.UUID,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> ContentBucket:
    """Retrieve a specific content bucket configuration by ID."""
    try:
        db_bucket = await service.get_bucket(bucket_id)
        if db_bucket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content bucket not found")
        return ContentBucket.from_orm(db_bucket)
    except Exception as e:
        logger.exception(f"Unexpected API error reading content bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.put("/{bucket_id}", response_model=ContentBucket)
async def update_content_bucket(
    bucket_id: uuid.UUID,
    bucket_in: ContentBucketUpdate,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> ContentBucket:
    """Update an existing content bucket configuration."""
    try:
        updated_bucket = await service.update_bucket(bucket_id, bucket_in)
        if updated_bucket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content bucket not found")
        return ContentBucket.from_orm(updated_bucket)
    except ServiceError as e:
        logger.error(f"API Error updating content bucket {bucket_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected API error updating content bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.delete("/{bucket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_bucket(
    bucket_id: uuid.UUID,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> None:
    """Delete a content bucket configuration."""
    try:
        deleted = await service.delete_bucket(bucket_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content bucket not found")
        return None # FastAPI handles 204
    except ServiceError as e:
        logger.error(f"API Error deleting content bucket {bucket_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected API error deleting content bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
