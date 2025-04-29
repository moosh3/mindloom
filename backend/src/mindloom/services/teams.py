# In backend/src/mindloom/services/teams.py
import uuid
import asyncio
import logging
import os
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Tuple
import agno
from agno.memory.team import TeamMemory as AgnoMemory
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.db.redis import RedisMemoryDb # <-- Import RedisMemory
from langchain_core.language_models.chat_models import BaseChatModel
from agno.embedder.base import Embedder # Added

# Agno imports
from agno.agent import Agent
from agno.team.team import Team
from agno.models.azure import AzureOpenAI
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.azure_openai import AzureOpenAIEmbedder
# Database/App imports
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from mindloom.app.models.team import TeamORM
from mindloom.app.models.agent import AgentORM
from mindloom.core.config import settings
from mindloom.services.agents import AgentService # Import AgentService
from mindloom.services.exceptions import ( # Import custom exceptions
    TeamCreationError,
    AgentCreationError,
    KnowledgeCreationError,
    StorageCreationError,
    ServiceError,
    ConfigurationError
)
from mindloom.app.models.content_bucket import ContentBucketORM # Import ContentBucketORM

if TYPE_CHECKING:
    from agno.knowledge.vectorstores.base import VectorStore

logger = logging.getLogger(__name__)

class TeamService:
    def __init__(self, db: AsyncSession, agent_service: "AgentService"): # Type hint AgentService
        self.db = db
        self.agent_service = agent_service
        # Store the engine for potential use by Agno components
        self.engine: AsyncEngine = db.bind
        if not self.engine:
            # This shouldn't happen if session is bound, but defensively check
            logger.error("Database session is not bound to an engine in TeamService.")
            raise ValueError("Database session is not bound to an engine.")

    async def get_team_config_from_db(self, team_id: uuid.UUID) -> Optional[TeamORM]:
        """Fetches the team's configuration record from the database, including agents."""
        stmt = (
            select(TeamORM)
            .where(TeamORM.id == team_id)
            # Use the correct relationship name from TeamORM
            .options(selectinload(TeamORM.agents)) # Eager load member AgentORMs
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    # --- Team-specific Component Creation --- 

    def _create_team_embedder(self, knowledge_config: Optional[Dict[str, Any]]) -> Optional[AzureOpenAIEmbedder]:
        """Creates the embedding model instance based on team's knowledge config."""
        # This logic is similar to AgentService._create_embedder
        if not knowledge_config or 'embedder' not in knowledge_config:
            logger.info("No embedder configuration found in team's knowledge_config. Team will not have shared knowledge.")
            return None
        
        embedder_conf = knowledge_config['embedder']
        provider = embedder_conf.get("provider", "azure_openai").lower()
        params = embedder_conf.get("params", {})

        if provider == "azure_openai":
            # Check API Key
            api_key_env_var = params.get("api_key_env_var", "AZURE_OPENAI_API_KEY")
            api_key = os.getenv(api_key_env_var)
            if not api_key:
                logger.error(f"Azure OpenAI API key env var '{api_key_env_var}' is not set for team embedder.")
                raise ConfigurationError(f"Azure OpenAI API key env var '{api_key_env_var}' is not set for team embedder.")

            # Check Endpoint
            azure_endpoint = params.get("azure_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT"))
            if not azure_endpoint:
                 logger.error("Azure OpenAI endpoint is not configured for team embedder in knowledge_config or AZURE_OPENAI_ENDPOINT env var.")
                 raise ConfigurationError("Azure OpenAI endpoint is not configured for team embedder.")

            # Check Embedding Deployment Name
            deployment_name = params.get("deployment_name", os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"))
            if not deployment_name:
                 logger.error("Azure OpenAI embedding deployment name is not configured for team embedder in knowledge_config or AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME env var.")
                 raise ConfigurationError("Azure OpenAI embedding deployment name is not configured for team embedder.")

            # Check API Version (Optional)
            api_version = params.get("api_version", os.getenv("AZURE_OPENAI_API_VERSION"))
            if not api_version:
                 logger.warning("Azure OpenAI API version is not configured for team embedder. Proceeding without it.")

            embedder_params = {
                "api_key": api_key,
                "azure_endpoint": azure_endpoint,
                "azure_deployment": deployment_name,
                "api_version": api_version,
                # Add other relevant AzureOpenAIEmbedder params if needed
            }
            embedder_params = {k: v for k, v in embedder_params.items() if v is not None}
            
            try:
                logger.info(f"Instantiating AzureOpenAIEmbedder for team with endpoint: {azure_endpoint}, deployment: {deployment_name}")
                return AzureOpenAIEmbedder(**embedder_params)
            except Exception as e:
                logger.error(f"Failed to instantiate team AzureOpenAIEmbedder: {e}", exc_info=True)
                # Wrap instantiation errors
                raise KnowledgeCreationError(f"Failed to instantiate team AzureOpenAIEmbedder: {e}") from e
        else:
             logger.error(f"Unsupported team embedder provider specified: {provider}")
             raise ConfigurationError(f"Unsupported team embedder provider: {provider}")

    async def _create_team_knowledge(self, team_orm: TeamORM, db: AsyncSession) -> Optional[PgVector]:
        """Creates the Agno Vector Store instance for the team and triggers sync.
        
        Returns the initialized (but potentially still syncing) VectorStore.
        """
        if not team_orm.knowledge_config:
            logger.info(f"Team {team_orm.id}: No knowledge_config provided. No vector store created.")
            return None
        
        # --- 1. Create Embedder --- #
        embedder = self._create_team_embedder(team_orm.knowledge_config)
        if not embedder:
             logger.error(f"Team {team_orm.id}: Cannot create vector store without embedder.")
             # Raise specific error for clarity
             raise KnowledgeCreationError(f"Team {team_orm.id}: Cannot create vector store without embedder.")

        # --- 2. Initialize Vector Store --- #
        vector_store_config = team_orm.knowledge_config.get("vector_store", {})
        # Use team ID for table name to avoid conflicts
        collection_name = vector_store_config.get("collection_name_prefix", "team_knowledge") + f"_{str(team_orm.id).replace('-', '_')}"
        connection_string = vector_store_config.get("connection_string", settings.DATABASE_URL_PSYCOPG)

        try:
            # Assuming PgVector is the desired store type for teams
            vector_store = PgVector(
                connection_string=connection_string,
                embedding_function=embedder,
                collection_name=collection_name,
                # Add other PgVector specific params if needed from vector_store_config
                logger=logger
            )
            logger.info(f"Team {team_orm.id}: Initialized PgVector store '{collection_name}'.")
            
            # --- 3. Trigger Background Sync (Placeholder) --- #
            # This part needs to be implemented to run potentially in background
            # For now, we'll call a synchronous placeholder
            # Ensure content_buckets are loaded before calling this
            await self._sync_team_vector_store(team_orm, vector_store, db)
            
            return vector_store
        except KnowledgeCreationError: # Propagate specific errors
             raise
        except Exception as e:
            logger.error(f"Team {team_orm.id}: Failed to instantiate or sync PgVector store '{collection_name}': {e}", exc_info=True)
            raise KnowledgeCreationError(f"Team {team_orm.id}: Failed to instantiate PgVector store '{collection_name}': {e}") from e

    async def _sync_team_vector_store(self, team_orm: TeamORM, vector_store: PgVector, db: AsyncSession):
        """Placeholder: Orchestrates syncing all associated S3 buckets to the team's vector store."""
        logger.info(f"Team {team_orm.id}: Starting vector store sync for collection '{vector_store.collection_name}'.")
        # TODO: Implement iteration over team_orm.content_buckets and call _sync_single_bucket_to_team_store
        if not team_orm.content_buckets:
            logger.info(f"Team {team_orm.id}: No content buckets associated, sync skipped.")
            return
            
        for bucket in team_orm.content_buckets:
            if bucket.bucket_type.lower() == 's3':
                try:
                     # TODO: Implement _sync_single_bucket_to_team_store
                     # await self._sync_single_bucket_to_team_store(team_orm, bucket, vector_store, db)
                     logger.info(f"Team {team_orm.id}: Placeholder sync for bucket {bucket.id}.") # Placeholder log
                except Exception as e:
                    logger.error(f"Team {team_orm.id}: Error syncing bucket {bucket.id} ('{bucket.name}'): {e}", exc_info=True)
                    # Decide whether to continue syncing other buckets or raise
            else:
                logger.warning(f"Team {team_orm.id}: Skipping sync for non-S3 bucket {bucket.id} ('{bucket.name}') type '{bucket.bucket_type}'.")

        logger.info(f"Team {team_orm.id}: Finished vector store sync process.")

    # Placeholder for the detailed sync logic per bucket
    async def _sync_single_bucket_to_team_store(self, db: AsyncSession, team_orm: TeamORM, bucket: ContentBucketORM, s3_client, team_vector_store: PgVector):
        """Handles the logic for syncing documents from a *specific* S3 bucket to the *team's shared* vector store."""
        s3_bucket_name = bucket.config.get('bucket_name')
        s3_prefix = bucket.config.get('prefix', '') # Handle potential prefix
        collection_name = team_vector_store.collection_name

        if not s3_bucket_name:
            logger.error(f"Team {team_orm.id}, Bucket {bucket.id}: S3 bucket_name not specified in config. Skipping sync.")
            return

        logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Starting sync with S3 bucket '{s3_bucket_name}', prefix '{s3_prefix}' into collection '{collection_name}'.")

        # Ensure bucket.files relation is loaded beforehand!
        if not hasattr(bucket, 'files') or bucket.files is None:
             logger.warning(f"Team {team_orm.id}, Bucket {bucket.id}: Files relationship not loaded or is None. Attempting explicit load. Ensure eager loading in caller for efficiency.")
             # Attempt explicit load (less efficient here)
             stmt = select(ContentBucketORM).where(ContentBucketORM.id == bucket.id).options(selectinload(ContentBucketORM.files))
             result = await db.execute(stmt)
             bucket = result.scalars().first()
             if not bucket or bucket.files is None:
                  logger.error(f"Team {team_orm.id}, Bucket {bucket.id}: Failed to explicitly load files relationship. Cannot sync.")
                  return # Cannot proceed without metadata

        db_files_for_this_bucket = {f.s3_key: f for f in bucket.files if f.s3_key}
        logger.debug(f"Team {team_orm.id}, Bucket {bucket.id}: Found {len(db_files_for_this_bucket)} file metadata records linked.")

        added_or_updated_docs = []
        processed_s3_keys = set()
        # Files in DB metadata (for this bucket) presumed deleted unless found in S3 list
        keys_to_delete_from_vector_store = set(db_files_for_this_bucket.keys())
        metadata_to_update = [] # Collect metadata records that need status updates

        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            # Ensure prefix ends with / if it's not empty and exists
            effective_prefix = s3_prefix
            if effective_prefix and not effective_prefix.endswith('/'):
                 effective_prefix += '/'
            
            logger.debug(f"Team {team_orm.id}, Bucket {bucket.id}: Listing objects with S3 prefix: '{effective_prefix}'")
            page_iterator = paginator.paginate(Bucket=s3_bucket_name, Prefix=effective_prefix)

            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    # Skip if the key exactly matches the prefix (it's the directory entry)
                    if s3_key == effective_prefix:
                        continue

                    # Basic check to ensure we are within the intended prefix (relevant if prefix is empty or root)
                    if effective_prefix and not s3_key.startswith(effective_prefix):
                         logger.warning(f"Team {team_orm.id}, Bucket {bucket.id}: S3 key '{s3_key}' listed but outside effective prefix '{effective_prefix}'. Skipping.")
                         continue

                    s3_last_modified = obj['LastModified']
                    s3_etag = obj['ETag'].strip('\"') # S3 ETags often have quotes
                    s3_size = obj['Size']

                    if s3_key.endswith('/') or s3_size == 0:
                        logger.debug(f"Team {team_orm.id}, Bucket {bucket.id}: Skipping S3 key '{s3_key}' (directory or empty file).")
                        continue # Skip directories/empty files

                    processed_s3_keys.add(s3_key)
                    keys_to_delete_from_vector_store.discard(s3_key) # Mark as present in S3 for this bucket

                    existing_metadata = db_files_for_this_bucket.get(s3_key)
                    needs_processing = False

                    if not existing_metadata:
                        # File exists in S3 bucket/prefix, but no FileMetadata record linked to this Team Bucket.
                        logger.warning(f"Team {team_orm.id}, Bucket {bucket.id}: S3 key '{s3_key}' found but no corresponding FileMetadata linked. Skipping processing. Register file via API if needed.")
                        continue # Skip processing this S3 object

                    # Ensure dates are timezone-aware (UTC) for comparison
                    metadata_last_modified_aware = existing_metadata.last_modified_at.replace(tzinfo=timezone.utc) if existing_metadata.last_modified_at else None
                    s3_last_modified_aware = s3_last_modified.replace(tzinfo=timezone.utc) if s3_last_modified else None
                    
                    if existing_metadata.s3_etag != s3_etag or \
                       (metadata_last_modified_aware and s3_last_modified_aware and metadata_last_modified_aware < s3_last_modified_aware) or \
                       existing_metadata.processing_status == 'error': # Reprocess if last attempt failed
                        logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Changed/New/Failed S3 file detected: {s3_key}. Processing. (DB ETag: {existing_metadata.s3_etag}, S3 ETag: {s3_etag}; DB Mod: {metadata_last_modified_aware}, S3 Mod: {s3_last_modified_aware}; Status: {existing_metadata.processing_status})")
                        needs_processing = True
                    elif existing_metadata.processing_status != 'processed':
                        logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: S3 file {s3_key} is up-to-date but was not 'processed'. Re-processing.")
                        needs_processing = True # Re-process if not successfully processed before
                    else:
                        logger.debug(f"Team {team_orm.id}, Bucket {bucket.id}: S3 file {s3_key} is up-to-date and processed.")

                    if needs_processing:
                        # Update metadata state before processing
                        existing_metadata.s3_etag = s3_etag
                        existing_metadata.last_modified_at = s3_last_modified # Store S3 timestamp (naive, S3 provides UTC)
                        existing_metadata.size_bytes = s3_size
                        existing_metadata.processing_status = 'processing' # Mark as processing
                        existing_metadata.processing_error = None # Clear previous error
                        metadata_to_update.append(existing_metadata)
                        await db.flush([existing_metadata]) # Flush to make 'processing' state visible sooner

                        with tempfile.TemporaryDirectory() as tmpdir:
                            # Use filename from metadata if available, otherwise basename of key
                            local_filename = existing_metadata.filename or os.path.basename(s3_key)
                            # Sanitize filename just in case
                            local_filename = local_filename.replace('/', '_').replace('\\', '_') 
                            local_file_path = os.path.join(tmpdir, local_filename)
                            doc_metadata_base = {}
                            current_file_processed = False
                            try:
                                logger.debug(f"Team {team_orm.id}, Bucket {bucket.id}: Downloading {s3_key} to {local_file_path}")
                                s3_client.download_file(s3_bucket_name, s3_key, local_file_path)
                                
                                # --- Metadata for Vector Store --- #
                                doc_metadata_base = {
                                    'source': s3_key,
                                    's3_bucket': s3_bucket_name,
                                    's3_etag': s3_etag,
                                    'content_bucket_id': str(bucket.id),
                                    'file_metadata_id': str(existing_metadata.id),
                                    'team_id': str(team_orm.id), # Add team context
                                    # Filterable keys for deletion/updates within the team's store
                                    'mindloom_content_bucket_id': str(bucket.id),
                                    'mindloom_s3_key': s3_key,
                                }
                                loaded_docs = load_document_from_file(local_file_path, existing_metadata.filename, doc_metadata_base)

                                if loaded_docs:
                                    logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Loaded {len(loaded_docs)} doc(s) from {s3_key}")
                                    # Delete existing docs for this *specific file* from *this bucket* before adding new/updated ones
                                    delete_filter = {
                                        'mindloom_content_bucket_id': str(bucket.id),
                                        'mindloom_s3_key': s3_key
                                    }
                                    try:
                                        logger.debug(f"Team {team_orm.id}, Bucket {bucket.id}: Deleting existing vector docs for {s3_key} using filter: {delete_filter}")
                                        team_vector_store.delete(filter=delete_filter)
                                        logger.debug(f"Team {team_orm.id}, Bucket {bucket.id}: Deletion complete for {s3_key}.")
                                    except Exception as del_exc:
                                        # Log deletion error but proceed with adding docs if possible
                                        logger.error(f"Team {team_orm.id}, Bucket {bucket.id}: Failed to delete existing vector docs for {s3_key}: {del_exc}", exc_info=True)
                                    
                                    added_or_updated_docs.extend(loaded_docs)
                                else:
                                    logger.warning(f"Team {team_orm.id}, Bucket {bucket.id}: No documents were loaded from file {s3_key}. Check loader compatibility.")
                                current_file_processed = True # Mark as successfully loaded/parsed
                            
                            except s3_client.exceptions.NoSuchKey:
                                 logger.warning(f"Team {team_orm.id}, Bucket {bucket.id}: S3 key '{s3_key}' not found during download (race condition?). Skipping.")
                                 existing_metadata.processing_status = 'error'
                                 existing_metadata.processing_error = 'S3 key not found during download'
                            except Exception as load_exc:
                                logger.error(f"Team {team_orm.id}, Bucket {bucket.id}: Failed to download or process file {s3_key}: {load_exc}", exc_info=True)
                                existing_metadata.processing_status = 'error'
                                existing_metadata.processing_error = f"Failed to download/process: {str(load_exc)[:250]}" # Store truncated error
                            finally:
                                if current_file_processed:
                                     existing_metadata.processing_status = 'processed'
                                     existing_metadata.processing_error = None
                                # Update metadata status regardless of success/failure during processing step
                                await db.flush([existing_metadata]) # Ensure status update is flushed

            # --- Add loaded documents in batches (if any) --- # 
            if added_or_updated_docs:
                try:
                    logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Adding/updating {len(added_or_updated_docs)} documents in vector store collection '{collection_name}'.")
                    team_vector_store.add_documents(added_or_updated_docs)
                    logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Successfully added/updated documents.")
                except Exception as add_exc:
                    logger.error(f"Team {team_orm.id}, Bucket {bucket.id}: Error adding documents to vector store: {add_exc}", exc_info=True)
                    # Mark relevant metadata as error?
                    for meta in metadata_to_update:
                         if meta.processing_status == 'processing': # Only mark those we tried to process in this batch
                              meta.processing_status = 'error'
                              meta.processing_error = f"Vector store add failed: {str(add_exc)[:200]}"
                    await db.flush(metadata_to_update) # Flush error status
            else:
                logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: No new or updated documents to add to vector store.")

            # --- Delete documents for files no longer in S3 (for this bucket) --- #
            if keys_to_delete_from_vector_store:
                logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Deleting documents for {len(keys_to_delete_from_vector_store)} keys not found in S3 listing: {keys_to_delete_from_vector_store}")
                # Construct filter for deletion: must match this bucket ID AND be one of the missing S3 keys
                delete_filter = {
                    '$and': [
                        {'mindloom_content_bucket_id': str(bucket.id)},
                        {'mindloom_s3_key': {'$in': list(keys_to_delete_from_vector_store)}}
                    ]
                }
                try:
                    team_vector_store.delete(filter=delete_filter)
                    logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Successfully deleted vectors for missing S3 keys.")
                    # Also delete the FileMetadata ORM records themselves for this bucket
                    # stmt_delete_meta = delete(FileMetadataORM).where(
                    #     FileMetadataORM.content_bucket_id == bucket.id,
                    #     FileMetadataORM.s3_key.in_(keys_to_delete_from_vector_store)
                    # )
                    # await db.execute(stmt_delete_meta)
                    # logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Deleted {len(keys_to_delete_from_vector_store)} FileMetadata records.")
                    # Decide if FileMetadata should be deleted or marked as inactive
                    # For now, just delete from vector store. Keep metadata record.
                    for s3_key_to_remove in keys_to_delete_from_vector_store:
                         if s3_key_to_remove in db_files_for_this_bucket:
                              meta_to_mark = db_files_for_this_bucket[s3_key_to_remove]
                              meta_to_mark.processing_status = 'deleted_from_s3'
                              meta_to_mark.processing_error = 'File removed from S3 source.'
                              metadata_to_update.append(meta_to_mark)
                    await db.flush(metadata_to_update)

                except Exception as del_exc:
                    logger.error(f"Team {team_orm.id}, Bucket {bucket.id}: Failed to delete vectors for missing S3 keys: {del_exc}", exc_info=True)
                    # Mark corresponding metadata as error?
                    for s3_key_to_remove in keys_to_delete_from_vector_store:
                         if s3_key_to_remove in db_files_for_this_bucket:
                              meta_to_mark = db_files_for_this_bucket[s3_key_to_remove]
                              meta_to_mark.processing_status = 'error'
                              meta_to_mark.processing_error = f'Vector delete failed: {str(del_exc)[:200]}'
                              metadata_to_update.append(meta_to_mark)
                    await db.flush(metadata_to_update)
            else:
                logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: No documents to delete from vector store for this bucket.")
        
        except s3_client.exceptions.NoSuchBucket:
            logger.error(f"Team {team_orm.id}, Bucket {bucket.id}: S3 bucket '{s3_bucket_name}' not found. Skipping sync.")
            # Mark all existing metadata for this bucket as error?
            for meta in db_files_for_this_bucket.values():
                 meta.processing_status = 'error'
                 meta.processing_error = f'S3 Bucket Not Found: {s3_bucket_name}'
                 metadata_to_update.append(meta)
            await db.flush(metadata_to_update)
        except Exception as e:
            logger.error(f"Team {team_orm.id}, Bucket {bucket.id}: An unexpected error occurred during S3 sync: {e}", exc_info=True)
            # Mark relevant metadata as error?
            for meta in metadata_to_update:
                if meta.processing_status == 'processing':
                    meta.processing_status = 'error'
                    meta.processing_error = f"Sync error: {str(e)[:200]}"
            await db.flush(metadata_to_update) # Ensure errors are flushed
            # Re-raise the error to be caught by the calling sync loop
            raise
        finally:
            # Ensure any final status updates are committed
            if metadata_to_update:
                 logger.debug(f"Team {team_orm.id}, Bucket {bucket.id}: Flushing final metadata updates.")
                 await db.flush(metadata_to_update)
            logger.info(f"Team {team_orm.id}, Bucket {bucket.id}: Finished sync process.")

    def _create_team_storage(
        self,
        team_orm: TeamORM,
        embedder: Optional[Embedder] = None # Added embedder parameter
    ) -> Optional[AgnoMemory]:
        """Creates the Agno Storage instance for the team. Defaults to RedisMemory if no config is provided."""
        storage_config = team_orm.storage_config
        team_id = team_orm.id # Use team ID for storage identification

        if not storage_config:
            logger.info(f"No storage_config for team {team_id}. Defaulting to Redis memory.")
            storage_config = {"type": "RedisMemoryDb"} # Default config
        
        storage_type = storage_config.get("type")
        params = storage_config.get("params", {})

        if not storage_type:
             logger.warning(f"Storage type missing in team {team_id}'s storage_config. Defaulting to RedisMemoryDb.")
             storage_type = "RedisMemoryDb"

        storage_type = storage_type.lower()

        try:
            if storage_type == "postgresmemorydb" or storage_type == "postgresagentstorage": # Handle legacy name
                db_url = params.get("db_url", settings.DATABASE_URL)
                if not db_url:
                     logger.error(f"Database URL not found in team {team_id} storage_config or app settings.")
                     raise ConfigurationError("Database URL for team storage not configured.")
                
                table_name = params.get("table_name", f"team_memory_{str(team_id).replace('-', '_')}")
                pg_config = {
                    "db_url": db_url,
                    "table_name": table_name,
                    "team_id": str(team_id) # Pass team_id for potential partitioning/indexing
                }
                logger.info(f"Instantiating PostgresMemoryDb for team {team_id} with table: {table_name}")
                return PostgresMemoryDb(**pg_config)
            
            elif storage_type == "redismemorydb":
                redis_url = params.get("redis_url", settings.REDIS_URL)
                if not redis_url:
                    logger.error(f"Redis URL not found in team {team_id} storage_config or app settings.")
                    raise ConfigurationError("Redis URL for team storage not configured.")
                # RedisMemoryDb requires an embedder
                if not embedder:
                    logger.error(f"Embedder instance required for RedisMemoryDb in team {team_id} but not provided.")
                    raise ConfigurationError(f"Embedder required for team {team_id}'s RedisMemoryDb storage.")

                # Use team_id for a unique key prefix in Redis
                key_prefix = params.get("key_prefix", f"mindloom:team_memory:{team_id}")
                redis_config = {
                    "redis_url": redis_url,
                    "key_prefix": key_prefix,
                    "embedder": embedder # Pass the embedder
                }
                logger.info(f"Instantiating RedisMemoryDb for team {team_id} with prefix: {key_prefix}")
                return RedisMemoryDb(**redis_config)

            else:
                logger.error(f"Unsupported storage type specified for team {team_id}: {storage_type}")
                raise ConfigurationError(f"Unsupported team storage type: {storage_type}")

        except ConfigurationError: # Re-raise config errors
            raise
        except Exception as e:
            logger.error(f"Failed to instantiate storage for team {team_id} with type {storage_type}: {e}", exc_info=True)
            raise StorageCreationError(f"Failed to instantiate storage for team {team_id}: {e}") from e

    def _create_team_leader_model(
        self,
        leader_model_config: Optional[Dict[str, Any]],
        team_id: uuid.UUID
    ) -> Tuple[Optional[BaseChatModel], Optional[Embedder]]: # Modified return type
        """Creates the Agno leader model instance based on leader_model_config."""
        if not leader_model_config:
            logger.warning(f"Team {team_id}: Leader model config missing. Cannot create leader model.")
            return None, None # Return None for both model and embedder

        model_type = leader_model_config.get("type")
        params = leader_model_config.get("params", {})
        # Extract embedder config if nested, or assume top-level params relate to embedder if separate config not present
        embedder_config = leader_model_config.get("embedder_config", params) 
        embedder_type = embedder_config.get("type", "AzureOpenAIEmbedder") # Default embedder

        logger.info(f"Team {team_id}: Creating leader model of type '{model_type}' with params: {params}")
        logger.info(f"Team {team_id}: Creating embedder of type '{embedder_type}' with params: {embedder_config.get('params', {})}")

        chat_model: Optional[BaseChatModel] = None
        embedder: Optional[Embedder] = None

        try:
            # Instantiate Embedder first (often needed by model or storage)
            if embedder_type == "AzureOpenAIEmbedder":
                azure_params = embedder_config.get("params", {})
                # Ensure required Azure params are present
                api_key = azure_params.get("api_key", settings.AZURE_OPENAI_API_KEY)
                endpoint = azure_params.get("endpoint", settings.AZURE_OPENAI_ENDPOINT)
                deployment_name = azure_params.get("deployment_name", settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME)
                api_version = azure_params.get("api_version", settings.AZURE_OPENAI_API_VERSION)

                if not all([api_key, endpoint, deployment_name, api_version]):
                    missing = [p for p, v in zip(['key', 'endpoint', 'deployment', 'version'], [api_key, endpoint, deployment_name, api_version]) if not v]
                    raise ConfigurationError(f"Team {team_id}: Missing Azure OpenAI embedder configuration: {', '.join(missing)}")
                
                embedder = AzureOpenAIEmbedder(
                    azure_deployment=deployment_name,
                    openai_api_key=api_key,
                    azure_endpoint=endpoint,
                    openai_api_version=api_version,
                    # Add other params like chunk_size if needed
                )
            # Add other embedder types here (e.g., OpenAIEmbedder)
            else:
                raise ConfigurationError(f"Team {team_id}: Unsupported embedder type specified: {embedder_type}")

            # Instantiate Chat Model
            if model_type == "AzureOpenAI":
                azure_params = params # Assuming params are for Azure Open AI Chat
                api_key = azure_params.get("api_key", settings.AZURE_OPENAI_API_KEY)
                endpoint = azure_params.get("endpoint", settings.AZURE_OPENAI_ENDPOINT)
                deployment_name = azure_params.get("deployment_name", settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME)
                api_version = azure_params.get("api_version", settings.AZURE_OPENAI_API_VERSION)

                if not all([api_key, endpoint, deployment_name, api_version]):
                     missing = [p for p, v in zip(['key', 'endpoint', 'deployment', 'version'], [api_key, endpoint, deployment_name, api_version]) if not v]
                     raise ConfigurationError(f"Team {team_id}: Missing Azure OpenAI chat model configuration: {', '.join(missing)}")

                chat_model = AzureOpenAI(
                    azure_deployment=deployment_name,
                    openai_api_key=api_key,
                    azure_endpoint=endpoint,
                    openai_api_version=api_version,
                    temperature=azure_params.get("temperature", 0.7), # Example param
                    # Add other AzureOpenAI specific params
                )
            # Add other model types here (e.g., OpenAI)
            else:
                raise ConfigurationError(f"Team {team_id}: Unsupported leader model type specified: {model_type}")
            
            return chat_model, embedder # Return both
        
        except ConfigurationError as e:
             logger.error(f"Team {team_id}: Configuration error creating leader model or embedder: {e}")
             raise # Re-raise specific configuration errors
        except Exception as e:
            logger.error(f"Team {team_id}: Failed to instantiate leader model '{model_type}' or embedder '{embedder_type}': {e}", exc_info=True)
            raise ModelCreationError(f"Team {team_id}: Failed to instantiate leader model/embedder: {e}") from e

    async def create_agno_team_instance(self, team_id: uuid.UUID) -> Team:
        """
        Fetches team config from DB, creates member agent instances, 
        and dynamically creates an Agno Team instance.
        Raises ValueError if team not found.
        Raises AgentCreationError if member agents cannot be instantiated.
        Raises TeamCreationError for issues during team component setup or instantiation.
         """
        logger.info(f"Creating Agno Team instance for ID: {team_id}")
        team_orm = await self.get_team_config_from_db(team_id)
        if not team_orm:
            logger.error(f"Team with ID {team_id} not found.")
            raise ValueError(f"Team with ID {team_id} not found.")
        
        # Use the correct relationship name
        if not team_orm.agents:
            logger.warning(f"Team with ID {team_id} has no member agents defined.")
            # Allow team creation with no agents for now

        # --- Instantiate Team Components --- #
        team_config_params = team_orm.team_config or {}

        # 1. Team Leader Model (Using refactored method)
        try:
            leader_model, leader_embedder = self._create_team_leader_model(team_orm.leader_model_config, team_id)
            if not leader_model:
                # Error logged in _create_leader_model
                raise TeamCreationError(f"Failed to create leader model for team {team_id}.")
        except (ConfigurationError, TeamCreationError) as e:
            logger.error(f"Failed to create leader model for team {team_id}: {e}")
            # Propagate the specific error
            raise TeamCreationError(f"Failed to create leader model for team {team_id}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating leader model for team {team_id}: {e}", exc_info=True)
            raise TeamCreationError(f"Unexpected error creating leader model for team {team_id}: {e}") from e

        # 2. Team Shared Knowledge (Vector Store)
        try:
            team_knowledge = await self._create_team_knowledge(team_orm, self.db)
        except KnowledgeCreationError as kce:
            logger.error(f"Team {team_id}: Failed to create team knowledge: {kce}")
            raise TeamCreationError(f"Failed to create knowledge for team {team_id}: {kce}") from kce
        
        # 3. Team Storage (Using refactored method)
        try:
            team_storage = self._create_team_storage(team_orm, embedder=leader_embedder) # Pass leader's embedder
        except StorageCreationError as sce:
            logger.error(f"Team {team_id}: Failed to create team storage: {sce}")
            raise TeamCreationError(f"Failed to create storage for team {team_id}: {sce}") from sce

        # --- Create Member Agent Instances --- 
        member_agents: List[Agent] = []
        failed_agent_ids = []
        if team_orm.agents:
            member_creation_tasks = []
            for member_agent_orm in team_orm.agents:
                # Pass the db session to the agent service method
                member_creation_tasks.append(
                    self.agent_service.create_agno_agent_instance(member_agent_orm.id, self.db)
                )
        
            # Execute tasks and handle exceptions
            results = await asyncio.gather(*member_creation_tasks, return_exceptions=True)
        
            # Process results, separating successes from failures
            for i, result in enumerate(results):
                if isinstance(result, Agent):
                    member_agents.append(result)
                elif isinstance(result, Exception):
                    failed_agent_id = team_orm.agents[i].id
                    failed_agent_ids.append(str(failed_agent_id))
                    logger.error(f"Failed to create member agent instance for team {team_id}: {result}", exc_info=result)
                else:
                    failed_agent_id = team_orm.agents[i].id
                    failed_agent_ids.append(str(failed_agent_id))
                    logger.warning(f"Got unexpected result type when creating member agent: {type(result)}")
        
            # If any agent creation failed, raise a specific error
            if len(member_agents) != len(team_orm.agents):
                logger.warning(f"Team {team_id}: Not all member agents could be instantiated.")
                error_msg = f"Failed to instantiate some member agents for team {team_id}. Failed IDs: {', '.join(failed_agent_ids)}"
                raise AgentCreationError(error_msg)
                # Depending on requirements, we might allow partial team creation

        # --- Prepare Agno Team Constructor Args --- 
        team_constructor_args = {
            "name": team_orm.name,
            "members": member_agents, # List of created Agent instances
            "model": leader_model,
            "mode": team_orm.mode, # Should be List[str]
            "knowledge": team_knowledge,
            "storage": team_storage,
            "description": team_orm.description,
            "instructions": team_orm.instructions,
            # Map params from team_config_params to Agno Team args
            'show_tool_calls': team_config_params.get('show_tool_calls', True),
            'markdown': team_config_params.get('markdown', False),
            'enable_agentic_context': team_config_params.get('enable_agentic_context', True),
            'share_member_interactions': team_config_params.get('share_member_interactions', True),
            # Add any other direct params Agno Team constructor accepts
        }

        # Remove None values for cleaner instantiation
        team_constructor_args = {k: v for k, v in team_constructor_args.items() if v is not None}

        # --- Instantiate Agno Team --- 
        try:
            logger.info(f"Instantiating Agno Team {team_id} with args: {list(team_constructor_args.keys())}")
            agno_team = Team(**team_constructor_args)
            logger.info(f"Successfully created Agno Team instance for ID: {team_id}")
            return agno_team
        except Exception as e:
            logger.error(f"Failed to instantiate Agno Team for ID {team_id}: {e}", exc_info=True)
            raise TeamCreationError(f"Failed to initialize Agno Team object for team {team_id}: {e}") from e

# --- Database Model Assumptions (TeamORM in mindloom.app.models.team) ---
# Needs fields like:
# - id: UUID
# - name: str
# - description: str
# - instructions: JSON list of strings? Or Text?
# - agents: Relationship to AgentORM (many-to-many)
# - llm_config: JSON (for team leader model, e.g., {"model_id": "gpt-4.1", ...})
# - mode: JSON list of strings (e.g., ["coordinate", "route"])
# - knowledge_config: JSON (optional, same format as agent's)
# - storage_config: JSON (optional, for team history, e.g., {"type": "PostgresAgentStorage", "table_name": "team_runs"})
# - team_config: JSON (e.g., {"markdown": false, "enable_agentic_context": true, ...})
# - enable_memory: bool
# - history_length: int

# --- Dependency Injection ---
# You'll need to ensure AgentService is available when creating TeamService.
# Example using FastAPI Depends:
#
# def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
#     return AgentService(db)
#
# def get_team_service(
#     db: AsyncSession = Depends(get_db),
#     agent_service: AgentService = Depends(get_agent_service)
# ) -> TeamService:
#     return TeamService(db, agent_service)
#
# @router.post("/{team_id}/run")
# async def run_team(
#     team_id: uuid.UUID,
#     # ... other inputs ...
#     team_service: TeamService = Depends(get_team_service)
# ):
#     session_id = uuid.uuid4() # Generate a unique session ID for this run
#     agno_team = await team_service.create_agno_team_instance(team_id)
#     # result = await agno_team.arun("User query")
#     # ...