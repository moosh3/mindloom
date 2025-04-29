import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession

from mindloom.dependencies import get_db, get_current_user
from mindloom.app.models.content_bucket import (
    ContentBucket,
    ContentBucketCreate,
    ContentBucketUpdate,
)
from mindloom.app.models.file_metadata import FileMetadata
from mindloom.services.content_buckets import ContentBucketService
from mindloom.services.exceptions import ServiceError

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])

def get_content_bucket_service(db: AsyncSession = Depends(get_db)) -> ContentBucketService:
    """Dependency injector for ContentBucketService."""
    return ContentBucketService(db)

@router.post("/", response_model=ContentBucket, status_code=status.HTTP_201_CREATED)
async def create_content_bucket(
    bucket_in: ContentBucketCreate,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> ContentBucket:
    """Create a new content bucket."""
    try:
        db_bucket = await service.create_bucket(bucket_in)
        return db_bucket
    except ServiceError as e:
        logger.error(f"Service error creating content bucket: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error creating content bucket: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/", response_model=List[ContentBucket])
async def read_content_buckets(
    skip: int = 0,
    limit: int = 100,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> List[ContentBucket]:
    """Retrieve a list of content buckets."""
    try:
        buckets = await service.get_buckets(skip=skip, limit=limit)
        return buckets
    except Exception as e:
        logger.exception(f"Unexpected error reading content buckets: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{bucket_id}", response_model=ContentBucket)
async def read_content_bucket(
    bucket_id: uuid.UUID,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> ContentBucket:
    """Retrieve a specific content bucket by ID."""
    try:
        bucket = await service.get_bucket(bucket_id)
        if bucket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content bucket not found")
        return bucket
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error reading content bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/{bucket_id}", response_model=ContentBucket)
async def update_content_bucket(
    bucket_id: uuid.UUID,
    bucket_in: ContentBucketUpdate,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> ContentBucket:
    """Update an existing content bucket."""
    try:
        updated_bucket = await service.update_bucket(bucket_id, bucket_in)
        if updated_bucket is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content bucket not found")
        return updated_bucket
    except ServiceError as e:
        logger.error(f"Service error updating content bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error updating content bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/{bucket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_bucket(
    bucket_id: uuid.UUID,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> Response:
    """Delete a content bucket by its ID."""
    try:
        deleted = await service.delete_bucket(bucket_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content bucket not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ServiceError as e:
        logger.error(f"Service error deleting content bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error deleting content bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/{bucket_id}/upload", response_model=FileMetadata, status_code=status.HTTP_201_CREATED)
async def upload_file(
    bucket_id: uuid.UUID,
    file: UploadFile = File(...),
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> FileMetadata:
    """Uploads a file to the specified content bucket (S3 type only)."""
    try:
        metadata = await service.upload_file_to_bucket(bucket_id, file)
        return metadata
    except ServiceError as e:
        logger.error(f"Service error uploading file to bucket {bucket_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error uploading file to bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{bucket_id}/files", response_model=List[Dict[str, Any]])
async def list_bucket_files(
    bucket_id: uuid.UUID,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> List[Dict[str, Any]]:
    """Lists files within the specified content bucket (S3 type only)."""
    try:
        files = await service.list_files(bucket_id)
        return files
    except ServiceError as e:
        logger.error(f"Service error listing files for bucket {bucket_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "not an S3 type" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error listing files for bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/{bucket_id}/files/{file_path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bucket_file(
    bucket_id: uuid.UUID,
    file_path: str,
    service: ContentBucketService = Depends(get_content_bucket_service),
) -> Response:
    """Deletes a specific file from the specified content bucket (S3 type only)."""
    try:
        success = await service.delete_file(bucket_id, file_path)
        if not success:
            logger.warning(f"delete_file service call returned False for bucket {bucket_id}, path {file_path}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ServiceError as e:
        logger.error(f"Service error deleting file '{file_path}' from bucket {bucket_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "not an S3 type" in str(e).lower() or "Invalid file path" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error deleting file '{file_path}' from bucket {bucket_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
