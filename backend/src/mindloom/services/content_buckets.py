import uuid
import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from mindloom.app.models.content_bucket import (
    ContentBucketORM,
    ContentBucketCreate,
    ContentBucketUpdate,
)
from mindloom.services.exceptions import ServiceError

logger = logging.getLogger(__name__)


class ContentBucketService:
    """Service layer for Content Bucket CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

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
        try:
            db_bucket = ContentBucketORM(**bucket_in.model_dump())
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
            return None  # Not found

        update_data = bucket_in.model_dump(exclude_unset=True)
        if not update_data:
            logger.warning(f"Update requested for bucket {bucket_id} but no data provided.")
            return db_bucket # Return existing if no changes

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
        # Optionally check if bucket exists first
        # db_bucket = await self.get_bucket(bucket_id)
        # if not db_bucket:
        #     logger.warning(f"Delete failed: Content bucket {bucket_id} not found.")
        #     return False
        
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
