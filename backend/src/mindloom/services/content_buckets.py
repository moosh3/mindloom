import uuid
import logging
import os
from datetime import datetime, timezone 
from typing import List, Optional, Dict, Any
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from mindloom.app.models.content_bucket import (
    ContentBucketORM,
    ContentBucketCreate,
    ContentBucketUpdate,
)
from mindloom.app.models.file_metadata import FileMetadataORM, FileMetadataCreate
from mindloom.services.exceptions import ServiceError

logger = logging.getLogger(__name__)

# Use aioboto3 for async operations if possible, but keeping boto3 for simplicity now
# from aiobotocore.session import get_session 

class ContentBucketService:
    """Service layer for Content Bucket CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        # Read S3 configuration from environment variables
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION')
        s3_endpoint_url = os.getenv('S3_ENDPOINT_URL') # Read optional endpoint URL

        s3_client_args = {
            'service_name': 's3',
            'aws_access_key_id': aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key,
            'region_name': aws_region
        }

        if s3_endpoint_url:
            logger.info(f"Using custom S3 endpoint URL: {s3_endpoint_url}")
            s3_client_args['endpoint_url'] = s3_endpoint_url
        else:
            logger.info("Using default AWS S3 endpoint.")

        self.s3_client = boto3.client(
            **s3_client_args
        )
        self.s3_bucket_name = os.getenv('S3_BUCKET_NAME')
        if not self.s3_bucket_name:
            logger.error("S3_BUCKET_NAME environment variable not set!")
            # Depending on requirements, could raise error or disable S3 features
            # raise ValueError("S3_BUCKET_NAME must be set")

    async def get_bucket(self, bucket_id: uuid.UUID) -> Optional[ContentBucketORM]:
        """Fetch a single content bucket by its ID."""
        logger.debug(f"Fetching content bucket with ID: {bucket_id}")
        statement = select(ContentBucketORM).where(ContentBucketORM.id == bucket_id)
        result = await self.db.execute(statement)
        bucket = result.scalars().first()
        if not bucket:
            logger.warning(f"Content bucket with ID {bucket_id} not found.")
        return bucket

    async def get_buckets(self, skip: int = 0, limit: int = 100) -> List[ContentBucketORM]:
        """Fetch a list of content buckets."""
        logger.debug(f"Fetching content buckets with skip={skip}, limit={limit}")
        statement = select(ContentBucketORM).offset(skip).limit(limit)
        result = await self.db.execute(statement)
        buckets = result.scalars().all()
        return buckets

    async def create_bucket(self, bucket_in: ContentBucketCreate) -> ContentBucketORM:
        """Create a new content bucket."""
        logger.info(f"Creating new content bucket: {bucket_in.name} (Type: {bucket_in.bucket_type})")
        
        bucket_id = uuid.uuid4()
        bucket_data = bucket_in.model_dump()

        if bucket_in.bucket_type == 'S3':
            s3_path = f"buckets/{bucket_id}/"  
            bucket_data['config']['s3_path'] = s3_path 
            logger.info(f"Generated S3 path for bucket {bucket_id}: {s3_path}")
        
        try:
            db_bucket = ContentBucketORM(id=bucket_id, **bucket_data)
            self.db.add(db_bucket)
            await self.db.commit()
            await self.db.refresh(db_bucket)
            logger.info(f"Successfully created content bucket {db_bucket.id} ('{db_bucket.name}')")
            return db_bucket
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error creating content bucket '{bucket_in.name}': {e}")
            raise ServiceError(f"Database error creating content bucket: {e}") from e

    async def update_bucket(
        self, bucket_id: uuid.UUID, bucket_in: ContentBucketUpdate
    ) -> Optional[ContentBucketORM]:
        """Update an existing content bucket."""
        logger.info(f"Updating content bucket with ID: {bucket_id}")
        db_bucket = await self.get_bucket(bucket_id)
        if not db_bucket:
            return None  

        update_data = bucket_in.model_dump(exclude_unset=True)
        if not update_data:
            logger.warning(f"Update requested for bucket {bucket_id} but no data provided.")
            return db_bucket 

        logger.debug(f"Applying update data to bucket {bucket_id}: {update_data}")
        for key, value in update_data.items():
            setattr(db_bucket, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(db_bucket)
            logger.info(f"Successfully updated content bucket {bucket_id}")
            return db_bucket
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error updating content bucket {bucket_id}: {e}")
            raise ServiceError(f"Database error updating content bucket: {e}") from e

    async def delete_bucket(self, bucket_id: uuid.UUID) -> bool:
        """Delete a content bucket by its ID. Returns True if deleted, False otherwise."""
        logger.info(f"Attempting to delete content bucket with ID: {bucket_id}")
        
        statement = delete(ContentBucketORM).where(ContentBucketORM.id == bucket_id)
        try:
            result = await self.db.execute(statement)
            await self.db.commit()
            if result.rowcount == 0:
                logger.warning(f"Delete failed: Content bucket {bucket_id} not found (rowcount 0)." )
                return False
            logger.info(f"Successfully deleted content bucket {bucket_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error deleting content bucket {bucket_id}: {e}")
            raise ServiceError(f"Database error deleting content bucket: {e}") from e

    async def upload_file_to_bucket(
        self, bucket_id: uuid.UUID, file: UploadFile
    ) -> FileMetadataORM:
        """Uploads a file to the S3 path associated with the bucket and creates metadata."""
        logger.info(f"Attempting to upload file '{file.filename}' to bucket {bucket_id}")

        if not self.s3_bucket_name:
             raise ServiceError("S3 Service not configured: S3_BUCKET_NAME not set.")

        db_bucket = await self.get_bucket(bucket_id)
        if not db_bucket:
            raise ServiceError(f"Content bucket {bucket_id} not found.")
        if db_bucket.bucket_type != 'S3':
            raise ServiceError(f"Bucket {bucket_id} is not an S3 type bucket.")

        s3_path_prefix = db_bucket.config.get('s3_path')
        if not s3_path_prefix:
            raise ServiceError(f"S3 path configuration missing for bucket {bucket_id}.")

        if file.filename is None:
            raise ServiceError("Uploaded file is missing a filename.")
        
        safe_filename = file.filename
        s3_key = f"{s3_path_prefix.rstrip('/')}/{safe_filename}"
        logger.debug(f"Target S3 Key: {s3_key} in bucket {self.s3_bucket_name}")

        try:
            self.s3_client.upload_fileobj(
                file.file,  
                self.s3_bucket_name,
                s3_key,
                ExtraArgs={'ContentType': file.content_type} 
            )
            logger.info(f"Successfully uploaded {safe_filename} to s3://{self.s3_bucket_name}/{s3_key}")
        except ClientError as e:
            logger.exception(f"S3 upload failed for {safe_filename} to bucket {bucket_id}: {e}")
            raise ServiceError(f"S3 upload failed: {e}")
        except Exception as e:
             logger.exception(f"Unexpected error during S3 upload for {safe_filename}: {e}")
             raise ServiceError(f"An unexpected error occurred during upload: {e}")

        try:
            file.file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0) 
            
            metadata_in = FileMetadataCreate(
                filename=safe_filename,
                s3_bucket=self.s3_bucket_name,
                s3_key=s3_key,
                content_type=file.content_type,
                size_bytes=file_size,
                last_modified=datetime.now(timezone.utc), 
                bucket_id=bucket_id,
            )
            db_metadata = FileMetadataORM(**metadata_in.model_dump())
            self.db.add(db_metadata)
            await self.db.commit()
            await self.db.refresh(db_metadata)
            logger.info(f"Successfully created FileMetadata {db_metadata.id} for {safe_filename}")
            return db_metadata
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error creating FileMetadata for {safe_filename} after S3 upload: {e}")
            raise ServiceError(f"Database error saving file metadata: {e}") from e

    async def list_files(self, bucket_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Lists files within the S3 path associated with the content bucket."""
        logger.info(f"Listing files for bucket {bucket_id}")

        if not self.s3_bucket_name:
            raise ServiceError("S3 Service not configured: S3_BUCKET_NAME not set.")

        db_bucket = await self.get_bucket(bucket_id)
        if not db_bucket:
            raise ServiceError(f"Content bucket {bucket_id} not found.")
        if db_bucket.bucket_type != 'S3':
            raise ServiceError(f"Bucket {bucket_id} is not an S3 type bucket.")

        s3_path_prefix = db_bucket.config.get('s3_path')
        if not s3_path_prefix:
            raise ServiceError(f"S3 path configuration missing for bucket {bucket_id}.")
        
        # Ensure prefix ends with a slash for proper directory listing
        if not s3_path_prefix.endswith('/'):
            s3_path_prefix += '/'

        listed_files = []
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.s3_bucket_name, Prefix=s3_path_prefix)

            for page in pages:
                if "Contents" in page:
                    for obj in page['Contents']:
                        # Exclude the directory marker itself if present
                        if obj['Key'] == s3_path_prefix:
                            continue
                        listed_files.append({
                            "key": obj['Key'],
                            "relative_path": obj['Key'][len(s3_path_prefix):], # Path relative to bucket prefix
                            "size": obj['Size'],
                            "last_modified": obj['LastModified']
                        })
            logger.info(f"Found {len(listed_files)} files in bucket {bucket_id} prefix {s3_path_prefix}")
            return listed_files
        except ClientError as e:
            logger.exception(f"S3 list objects failed for bucket {bucket_id} prefix {s3_path_prefix}: {e}")
            raise ServiceError(f"S3 list objects failed: {e}")
        except Exception as e:
             logger.exception(f"Unexpected error listing files for bucket {bucket_id}: {e}")
             raise ServiceError(f"An unexpected error occurred while listing files: {e}")

    async def delete_file(self, bucket_id: uuid.UUID, file_path: str) -> bool:
        """Deletes a specific file from the S3 path associated with the bucket and its metadata."""
        logger.info(f"Attempting to delete file '{file_path}' from bucket {bucket_id}")

        if not self.s3_bucket_name:
            raise ServiceError("S3 Service not configured: S3_BUCKET_NAME not set.")

        db_bucket = await self.get_bucket(bucket_id)
        if not db_bucket:
            raise ServiceError(f"Content bucket {bucket_id} not found.")
        if db_bucket.bucket_type != 'S3':
            raise ServiceError(f"Bucket {bucket_id} is not an S3 type bucket.")

        s3_path_prefix = db_bucket.config.get('s3_path')
        if not s3_path_prefix:
            raise ServiceError(f"S3 path configuration missing for bucket {bucket_id}.")
        
        # Basic path validation/normalization to prevent escaping the bucket prefix
        # Remove leading slash if present and resolve any '.' or '..' components safely
        # Using posixpath explicitly to handle S3 keys correctly
        import posixpath
        normalized_file_path = posixpath.normpath(posixpath.join('/', file_path.lstrip('/'))).lstrip('/')
        if '..' in normalized_file_path.split('/'):
             logger.error(f"Invalid file path contains '..': {file_path}")
             raise ServiceError("Invalid file path specified.")
        
        s3_key = f"{s3_path_prefix.rstrip('/')}/{normalized_file_path}"
        logger.debug(f"Target S3 Key for deletion: {s3_key} in bucket {self.s3_bucket_name}")

        # 1. Delete from S3
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=s3_key)
            logger.info(f"Successfully deleted {s3_key} from S3 bucket {self.s3_bucket_name}")
        except ClientError as e:
            # Check if it's a 'NoSuchKey' error - often okay during delete, means already gone
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"S3 delete object skipped for key {s3_key}: Key does not exist.")
                # Proceed to delete metadata, as the file isn't in S3 anyway
                pass 
            else:
                logger.exception(f"S3 delete object failed for key {s3_key}: {e}")
                raise ServiceError(f"S3 delete object failed: {e}")
        except Exception as e:
             logger.exception(f"Unexpected error during S3 delete for key {s3_key}: {e}")
             raise ServiceError(f"An unexpected error occurred during S3 deletion: {e}")

        # 2. Delete metadata from DB (best effort - S3 delete already happened or key didn't exist)
        try:
            stmt = delete(FileMetadataORM).where(
                FileMetadataORM.bucket_id == bucket_id,
                FileMetadataORM.s3_key == s3_key # Match the exact key we attempted to delete
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            if result.rowcount > 0:
                 logger.info(f"Successfully deleted {result.rowcount} FileMetadata record(s) for key {s3_key}")
            else:
                 logger.warning(f"No FileMetadata record found for S3 key {s3_key} in bucket {bucket_id} during delete operation.")
            return True # Return True as the state (file gone from S3) is achieved
        except Exception as e:
            await self.db.rollback()
            # Log error but don't necessarily raise? S3 file is gone/wasn't there.
            logger.exception(f"Error deleting FileMetadata for key {s3_key} after S3 operation: {e}")
            # Depending on strictness, could raise or return False.
            # Returning True because S3 state is correct. Frontend can check metadata if needed.
            return True
