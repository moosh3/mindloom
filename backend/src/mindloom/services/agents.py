"""
Provides a wrapper around Agno for handling the lifecycle of agents.
"""
import uuid
import importlib
import inspect
from typing import List, Optional, Dict, Any
from textwrap import dedent
import logging
from datetime import datetime

# Agno imports
from agno.agent import Agent
from agno.embedder.azure_openai import AzureOpenAIEmbedder
from agno.knowledge.text import TextKnowledgeBase # <-- Add if missing
from agno.models.azure import AzureOpenAI
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.tools.toolkit import Toolkit # <-- Corrected capitalization
from agno.vectordb.pgvector import PgVector, SearchType # <-- Add PgVector, SearchType if missing

# Langchain imports for loading (ensure these are present)
from langchain_core.documents import Document

# Database/App imports (ensure these are present)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound
from mindloom.app.models.agent import AgentORM, ToolConfig
from mindloom.app.models.content_bucket import ContentBucketORM
from mindloom.app.models.file_metadata import FileMetadataORM
from mindloom.core.config import settings

# Local utils import
from .utils import camel_to_snake, get_s3_client, load_document_from_file

# Logging (ensure logger is configured, e.g., logging.getLogger(__name__))
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.app_settings = settings

    async def get_agent_config_from_db(self, agent_id: uuid.UUID) -> Optional[AgentORM]:
        """Fetches the agent's configuration record from the database."""
        statement = select(AgentORM).where(AgentORM.id == agent_id)
        result = await self.db.execute(statement)
        return result.scalars().first()

    async def create_agno_agent_instance(
        self,
        agent_id: uuid.UUID,
        session_id: uuid.UUID
    ) -> Agent:
        """
        Fetches config from DB (including linked Content Buckets) and dynamically
        creates an Agno agent instance with configured model, tools, knowledge bases,
        and storage.
        """
        async with self.db as session:
            try:
                # Fetch AgentORM with related data eagerly loaded
                statement = select(AgentORM).where(AgentORM.id == agent_id)
                statement = statement.options(
                    selectinload(AgentORM.variables),
                    selectinload(AgentORM.content_buckets).selectinload(ContentBucketORM.files) # Eager load buckets and their files
                )
                result = await session.execute(statement)
                agent_orm = result.scalars().one() # Use one() for stricter check
            except NoResultFound:
                logging.error(f"Agent configuration not found for agent_id: {agent_id}")
                raise ValueError(f"Agent configuration not found for agent_id: {agent_id}")
            except Exception as e:
                logging.error(f"Error fetching agent configuration for {agent_id}: {e}", exc_info=True)
                raise

            # --- Instantiate Components --- #

            # 1. Language Model
            agno_model = self._create_model(agent_orm.llm_config)

            # 2. Tools
            agno_tools = self._create_tools(agent_orm.tools) 

            # 3. Knowledge Bases (Vector Store + Embedder per bucket)
            # Call the renamed method which will return a list of KnowledgeBase objects
            agno_knowledge = await self._create_knowledge_bases(agent_orm, session)

            # 4. Storage
            agno_storage = self._create_storage(agent_orm.storage_config)

            agent_params = agent_orm.agent_config or {}

            agno_agent = Agent(
                name=agent_orm.name,
                agent_id=agent_orm.id,
                session_id=session_id,

                model=agno_model,
                tools=agno_tools,
                knowledge=agno_knowledge,
                storage=agno_storage,

                description=agent_orm.description,
                instructions=agent_orm.instructions, 
                additional_context=agent_params.get("additional_context", ""),
                markdown=agent_params.get("markdown", False),
                num_history_reponses=agent_params.get("num_history_reponses", 5),
                clear_history_on_new_session=agent_params.get("clear_history_on_new_session", True),
                enable_semantic_memory=agent_params.get("enable_semantic_memory", True),
                enable_episodic_memory=agent_params.get("enable_episodic_memory", True),
                allow_user_interaction=agent_params.get("allow_user_interaction", True),
                **{k: v for k, v in agent_params.items() if k not in [
                    "additional_context", "markdown", "num_history_reponses",
                    "clear_history_on_new_session", "enable_semantic_memory",
                    "enable_episodic_memory", "allow_user_interaction"
                ]} 
            )

            return agno_agent

    def _create_model(self, llm_config: Optional[Dict[str, Any]]) -> Optional[AzureOpenAI]:
        """Creates the Agno LLM instance based on llm_config."""
        if not llm_config:
            print("Warning: No llm_config provided for agent.")
            return None 

        model_provider = llm_config.get("provider", "azure").lower()

        if model_provider == "azure":
            api_key = self.app_settings.AZURE_OPENAI_API_KEY
            api_base = self.app_settings.AZURE_OPENAI_API_BASE
            if not api_key or not api_base:
                raise ValueError("Azure OpenAI API Key or Base URL not configured in settings.")

            model_id = llm_config.get("model_id")
            deployment_name = llm_config.get("deployment_name", model_id) 
            api_version = llm_config.get("api_version", "2023-12-01-preview") 
            temperature = llm_config.get("temperature", 0.7)
            model_kwargs = llm_config.get("model_kwargs", {}) 

            if not model_id:
                raise ValueError("Missing 'model_id' in llm_config for Azure provider.")

            return AzureOpenAI(
                model_id=model_id,
                deployment_name=deployment_name,
                api_version=api_version,
                api_key=api_key,
                api_base=api_base,
                temperature=temperature,
                model_kwargs=model_kwargs
            )
        else:
            raise NotImplementedError(f"LLM provider '{model_provider}' not yet supported.")

    def _create_tools(self, tool_configs: Optional[List[Dict[str, Any]]]) -> List[Toolkit]:
        """Dynamically imports and instantiates Toolkit classes based on names and config from DB."""
        instance_tools: List[Toolkit] = []
        if not tool_configs:
            return instance_tools

        for tool_conf in tool_configs:
            tool_name = tool_conf.get("name")
            tool_config_params = tool_conf.get("config", {})

            if not tool_name:
                print("Warning: Tool entry missing 'name'. Skipping.")
                continue

            try:
                module_name = f"mindloom.tools.{camel_to_snake(tool_name)}"
                tool_module = importlib.import_module(module_name)

                ToolkitClass = getattr(tool_module, tool_name, None)

                if ToolkitClass and inspect.isclass(ToolkitClass) and issubclass(ToolkitClass, Toolkit):
                    tool_instance = ToolkitClass(**tool_config_params)
                    instance_tools.append(tool_instance)
                else:
                    print(f"Warning: Toolkit class '{tool_name}' not found or invalid in module '{module_name}'. Skipping.")

            except ModuleNotFoundError:
                print(f"Warning: Tool module '{module_name}' for tool '{tool_name}' not found. Skipping.")
            except Exception as e:
                print(f"Warning: Error instantiating tool '{tool_name}' with config {tool_config_params}: {e}. Skipping.")

        return instance_tools

    # Replace the old _create_knowledge method with this one
    async def _create_knowledge_bases(self, agent_orm: AgentORM, db: AsyncSession) -> List[TextKnowledgeBase]:
        """
        Dynamically instantiates KnowledgeBase objects for each linked Content Bucket,
        configures them with embedders and vector stores, and syncs documents.
        """
        logger.info(f"Agent {agent_orm.id}: Starting knowledge base creation for {len(agent_orm.content_buckets)} linked buckets.")
        created_knowledge_bases: List[TextKnowledgeBase] = []

        if not agent_orm.content_buckets:
            logger.info(f"Agent {agent_orm.id}: No content buckets linked. No knowledge bases to create.")
            return []

        for bucket in agent_orm.content_buckets:
            logger.info(f"Agent {agent_orm.id}: Processing bucket {bucket.id} ('{bucket.name}', type: {bucket.bucket_type})")

            # --- 1. Create Embedder for this Bucket --- #
            embedder = self._create_embedder(bucket.embedder_config)
            if not embedder:
                logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Failed to create embedder. Skipping this knowledge base.")
                continue # Skip to next bucket
            logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Embedder '{type(embedder).__name__}' created successfully.")

            # --- 2. Create Vector Store (PgVector) for this Bucket --- #
            vector_db_config = bucket.vector_db_config or {}
            search_type_str = vector_db_config.get('search_type', 'similarity').lower()
            search_type = SearchType.SIMILARITY if search_type_str == 'similarity' else SearchType.MMR
            search_k = vector_db_config.get('search_k', 4)
            # Define a unique collection name PER BUCKET
            collection_name = f"agent_{str(agent_orm.id).replace('-', '')}_bucket_{str(bucket.id).replace('-', '')}"
            logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Using vector store collection name: {collection_name}")

            try:
                vector_store = PgVector(
                    connection_string=str(self.app_settings.DATABASE_URL),
                    collection_name=collection_name,
                    embedder=embedder,
                    search_type=search_type,
                    search_k=search_k,
                    logger=logger # Pass logger instance
                )
                logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: PgVector store instance created/connected for collection '{collection_name}'.")
            except Exception as e:
                logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Failed to initialize PgVector: {e}", exc_info=True)
                continue # Skip this bucket

            # --- 3. Instantiate KnowledgeBase (Example: TextKnowledgeBase) --- #
            # TODO: Implement factory or conditional logic based on bucket.bucket_type
            knowledge_base_instance = None
            if bucket.bucket_type.lower() == 's3':
                try:
                    knowledge_base_instance = TextKnowledgeBase(
                        name=f"kb_{bucket.name.replace(' ', '_')}_{str(bucket.id)[:8]}", # Unique KB name
                        description=bucket.description or f"Knowledge from S3 bucket {bucket.name}",
                        vector_store=vector_store,
                        embedder=embedder,
                        logger=logger # Pass logger if KB accepts it
                    )
                    logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: TextKnowledgeBase instance '{knowledge_base_instance.name}' created.")
                except Exception as e:
                    logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Failed to instantiate TextKnowledgeBase: {e}", exc_info=True)
                    continue # Skip this bucket
            # Add elif blocks here for other bucket types (e.g., 'URL', 'Local')
            # elif bucket.bucket_type.lower() == 'url':
            #    knowledge_base_instance = URLKnowledgeBase(...) # Assuming such a class exists
            else:
                logger.warning(f"Agent {agent_orm.id}, Bucket {bucket.id}: Unsupported bucket type '{bucket.bucket_type}'. Skipping knowledge base creation.")
                continue # Skip this bucket

            # --- 4. Load/Update Documents for this Bucket (Example: S3) --- #
            if bucket.bucket_type.lower() == 's3':
                bucket_config = bucket.config or {}
                s3_bucket_name = bucket_config.get('bucket_name')
                storage_credentials = bucket_config.get('storage_credentials') # Bucket-specific creds

                if not s3_bucket_name:
                    logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: S3 bucket_name not specified in config. Skipping document sync for this bucket.")
                    # Still add the KB instance, even if empty initially
                else:
                    s3_client = get_s3_client(storage_credentials) # Use bucket creds if provided
                    if not s3_client:
                        logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Failed to get S3 client. Cannot sync documents for this bucket.")
                        # Still add the KB instance
                    else:
                        logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Syncing documents from S3 bucket '{s3_bucket_name}' into collection '{collection_name}'.")
                        try:
                           await self._sync_s3_documents_for_bucket(db, agent_orm, bucket, s3_client, vector_store)
                        except Exception as e:
                            # Log error but don't stop processing other buckets
                            logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Unexpected error during document sync: {e}", exc_info=True)

            # Add the successfully created (even if empty) knowledge base instance
            if knowledge_base_instance:
                created_knowledge_bases.append(knowledge_base_instance)
            # --- End of bucket loop --- #

        logger.info(f"Agent {agent_orm.id}: Finished processing buckets. Created {len(created_knowledge_bases)} knowledge base instances.")
        return created_knowledge_bases

    # Add this new method to the AgentService class
    async def _sync_s3_documents_for_bucket(self, db: AsyncSession, agent_orm: AgentORM, bucket: ContentBucketORM, s3_client, vector_store: PgVector):
        """Handles the logic for syncing documents from a specific S3 bucket to its vector store."""
        s3_bucket_name = bucket.config.get('bucket_name')
        s3_prefix = bucket.config.get('prefix', '')
        collection_name = vector_store.collection_name # Get collection name from store

        # Use the eager-loaded files associated with the specific bucket
        db_files = {f.s3_key: f for f in bucket.files if f.s3_key} # Files associated ONLY with this bucket
        logger.debug(f"Agent {agent_orm.id}, Bucket {bucket.id}: Found {len(db_files)} file metadata records linked.")

        added_or_updated_docs = []
        processed_s3_keys = set()
        # Assume all files currently in metadata need deletion unless found/updated in S3
        keys_to_delete_from_vector_store = set(db_files.keys())
        metadata_to_update = [] # Collect metadata records that need status updates

        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=s3_bucket_name, Prefix=s3_prefix)

            for page in page_iterator:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    s3_key = obj['Key']
                    s3_last_modified = obj['LastModified']
                    s3_etag = obj['ETag'].strip('\"')
                    s3_size = obj['Size']

                    if s3_key.endswith('/') or s3_size == 0:
                        continue # Skip directories/empty files

                    processed_s3_keys.add(s3_key)
                    keys_to_delete_from_vector_store.discard(s3_key) # Mark as present in S3

                    existing_metadata = db_files.get(s3_key)
                    needs_processing = False

                    if not existing_metadata:
                        # This case implies an inconsistency: S3 object exists but no FileMetadata
                        # linked to this bucket via the association table. This shouldn't happen
                        # if the Bucket/File API manages the association correctly.
                        logger.warning(f"Agent {agent_orm.id}, Bucket {bucket.id}: S3 key '{s3_key}' found during sync but no corresponding FileMetadata linked to this bucket via association. Skipping processing. Ensure file registration is correct.")
                        continue # Skip processing this S3 object

                    # Check if update needed based on ETag or last modified time
                    if existing_metadata.s3_etag != s3_etag or \
                       (existing_metadata.last_modified_at and existing_metadata.last_modified_at < s3_last_modified):
                        logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Updated S3 file detected: {s3_key}. Processing.")
                        needs_processing = True
                    else:
                        logger.debug(f"Agent {agent_orm.id}, Bucket {bucket.id}: S3 file {s3_key} is up-to-date.")

                    if needs_processing:
                        # Update metadata state before processing
                        existing_metadata.s3_etag = s3_etag
                        existing_metadata.last_modified_at = s3_last_modified
                        existing_metadata.size = s3_size
                        existing_metadata.processing_status = 'processing' # Mark as processing
                        existing_metadata.processing_error = None # Clear previous error
                        metadata_to_update.append(existing_metadata)

                        with tempfile.TemporaryDirectory() as tmpdir:
                            local_file_path = os.path.join(tmpdir, existing_metadata.filename or os.path.basename(s3_key))
                            try:
                                logger.debug(f"Agent {agent_orm.id}, Bucket {bucket.id}: Downloading {s3_key} to {local_file_path}")
                                s3_client.download_file(s3_bucket_name, s3_key, local_file_path)
                                # Add bucket-specific metadata for context/filtering
                                doc_metadata_base = {
                                    'source': s3_key,
                                    's3_bucket': s3_bucket_name,
                                    's3_etag': s3_etag,
                                    'content_bucket_id': str(bucket.id),
                                    'file_metadata_id': str(existing_metadata.id),
                                    # Add a filterable key for deletion
                                    'mindloom_s3_key': s3_key,
                                    'mindloom_content_bucket_id': str(bucket.id)
                                }
                                loaded_docs = load_document_from_file(local_file_path, existing_metadata.filename, doc_metadata_base)

                                if loaded_docs:
                                    logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Loaded {len(loaded_docs)} doc(s) from {s3_key}")
                                    added_or_updated_docs.extend(loaded_docs)
                                    existing_metadata.processing_status = 'processed'
                                else:
                                    logger.warning(f"Agent {agent_orm.id}, Bucket {bucket.id}: No documents loaded from {s3_key}. Marking failed.")
                                    existing_metadata.processing_status = 'failed'
                                    existing_metadata.processing_error = 'No documents loaded by Langchain loader.'

                            except ClientError as e:
                                logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: S3 Error downloading {s3_key}: {e}", exc_info=True)
                                existing_metadata.processing_status = 'failed'
                                existing_metadata.processing_error = f"S3 ClientError: {e}"
                            except Exception as e:
                                logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Error processing file {s3_key}: {e}", exc_info=True)
                                existing_metadata.processing_status = 'failed'
                                existing_metadata.processing_error = f"Processing error: {e}"
                            finally:
                                existing_metadata.last_processed_at = datetime.utcnow()

        except ClientError as e:
             logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: S3 Error listing objects: {e}", exc_info=True)
             # Don't proceed with vector store updates if listing failed
             return
        except Exception as e:
             logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Unexpected error during S3 listing/processing: {e}", exc_info=True)
             # Optionally decide whether to proceed based on error type
             return

        # --- Delete vectors for files no longer in S3 (or removed from bucket metadata) --- #
        if keys_to_delete_from_vector_store:
            logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Found {len(keys_to_delete_from_vector_store)} keys in metadata no longer present in S3 prefix '{s3_prefix}'. Deleting corresponding vectors from collection '{collection_name}'.")
            try:
                # Delete from vector store using the specific key we added
                delete_filter = {'mindloom_s3_key': {'$in': list(keys_to_delete_from_vector_store)}}
                vector_store.delete(filter=delete_filter)
                logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Successfully submitted deletion request for vectors associated with removed S3 keys.")
                # NOTE: Actual deletion of FileMetadataORM records should happen via the Bucket API
                # when a file is removed from a bucket, not automatically here.
            except Exception as e:
                logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Error deleting vectors for removed S3 keys: {e}", exc_info=True)

        # --- Add/Update documents in this bucket's vector store --- #
        if added_or_updated_docs:
            logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Adding/updating {len(added_or_updated_docs)} documents in vector store collection '{collection_name}'.")
            try:
                # Delete existing vectors for the specific files being updated in this bucket
                updated_keys = {doc.metadata['mindloom_s3_key'] for doc in added_or_updated_docs}
                if updated_keys:
                     logger.debug(f"Agent {agent_orm.id}, Bucket {bucket.id}: Deleting existing vectors for updated keys: {updated_keys}")
                     delete_filter = {'mindloom_s3_key': {'$in': list(updated_keys)}}
                     vector_store.delete(filter=delete_filter)

                vector_store.add_documents(added_or_updated_docs)
                logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: Successfully added/updated documents in vector store.")
            except Exception as e:
                 logger.error(f"Agent {agent_orm.id}, Bucket {bucket.id}: Error adding documents to vector store: {e}", exc_info=True)
        else:
            logger.info(f"Agent {agent_orm.id}, Bucket {bucket.id}: No documents were processed for addition/update in this sync.")

        # Note: We don't commit here. The calling method handles the overall session commit.
        # We flush to ensure status updates are pushed to the DB before the commit.
        if metadata_to_update:
             logger.debug(f"Agent {agent_orm.id}, Bucket {bucket.id}: Flushing {len(metadata_to_update)} metadata updates.")
             await db.flush(metadata_to_update)

    def _create_embedder(self, knowledge_config: Optional[Dict[str, Any]]) -> Optional[AzureOpenAIEmbedder]:
        """Creates the embedding model instance based on knowledge config."""
        if not knowledge_config or 'embedder' not in knowledge_config:
            logging.info("No embedder configuration found in knowledge_config.")
            return None

        embedder_conf = knowledge_config['embedder']
        provider = embedder_conf.get("provider", "azure_openai") # Default or get from config
        params = embedder_conf.get("params", {})

        # Example: Azure OpenAI Embedder
        if provider.lower() == "azure_openai":
            api_key = os.getenv(params.get("api_key_env_var"))
            if not api_key:
                logging.warning(f"Env var {params.get('api_key_env_var')} not set for Azure OpenAI embedder.")
                # Decide if this is critical - maybe raise error or return None
                # return None
            
            # Filter params for the constructor - adjust based on AzureOpenAIEmbedder signature
            embedder_params = {
                "api_key": api_key,
                "azure_endpoint": params.get("azure_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT")),
                "api_version": params.get("api_version", os.getenv("AZURE_OPENAI_API_VERSION")),
                "azure_deployment": params.get("deployment_name", os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")),
                # Add other relevant params like chunk_size etc.
            }
            # Remove None values
            embedder_params = {k: v for k, v in embedder_params.items() if v is not None}

            try:
                return AzureOpenAIEmbedder(**embedder_params)
            except Exception as e:
                logging.error(f"Failed to instantiate AzureOpenAIEmbedder: {e}")
                return None
        else:
            logging.warning(f"Unsupported embedder provider: {provider}")
            return None

    def _create_storage(self, storage_config: Optional[Dict[str, Any]]) -> Optional[PostgresAgentStorage]:
         """Creates the Agno Storage instance based on storage_config."""
         if not storage_config:
             storage_config = {"type": "PostgresAgentStorage", "table_name": "agent_runs"} 

         storage_type = storage_config.get("type", "PostgresAgentStorage")

         if storage_type == "PostgresAgentStorage":
             table_name = storage_config.get("table_name", "agent_runs") 
             return PostgresAgentStorage(
                 db_url=str(self.app_settings.DATABASE_URL),
                 table_name=table_name
             )
         else:
             logging.warning(f"Unsupported storage type: {storage_type}")
             return None