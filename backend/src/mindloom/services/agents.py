"""
Provides a wrapper around Agno for handling the lifecycle of agents.
"""
import uuid
import importlib
import inspect
import os
from typing import List, Optional, Dict, Any
from textwrap import dedent
import logging
from datetime import datetime, timezone
import tempfile

# Agno imports
from agno.agent import Agent
from agno.embedder.base import Embedder
from agno.embedder.azure_openai import AzureOpenAIEmbedder
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.agent import AgentKnowledge
from agno.knowledge.text import TextKnowledgeBase
from agno.knowledge.s3.pdf import S3PDFKnowledgeBase
from agno.models.azure import AzureOpenAI
from agno.models.openai import OpenAIChat as OpenAI  # Added
from agno.models.base import Model
from agno.memory.v2.db.redis import RedisMemoryDb
from agno.storage.postgres import PostgresStorage # Correct import
from agno.tools.toolkit import Toolkit
from agno.vectordb.base import VectorDb
from agno.vectordb.chroma import ChromaDb
from agno.vectordb.pgvector import PgVector
from agno.embedder.base import Embedder

# Langchain imports for loading
from langchain_core.documents import Document

# Database/App imports
from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound
from mindloom.app.models.agent import AgentORM, ToolConfig
from mindloom.app.models.content_bucket import ContentBucketORM
from mindloom.app.models.file_metadata import FileMetadataORM
from mindloom.core.config import settings
from mindloom.db.session import get_async_db_engine
from mindloom.services.exceptions import (
    AgentRunError,
    KnowledgeCreationError,
    StorageCreationError,
    ToolCreationError,
    ModelCreationError,
    ConfigurationError,
    ServiceError,
    EmbedderCreationError,
    VectorStoreCreationError
)

# Local utils import
from .utils import camel_to_snake, get_s3_client, load_document_from_file

# Logging (ensure logger is configured, e.g., logging.getLogger(__name__))
logger = logging.getLogger(__name__)

def _tool_name_to_module_name(tool_class_name: str) -> str:
    """Converts a tool class name like 'GithubTools' to its module name 'github'."""
    if tool_class_name.endswith("Tools"): # Standard convention
        return tool_class_name[:-len("Tools")].lower()
    # Fallback for names not ending in 'Tools'
    logger.warning(f"Tool class name '{tool_class_name}' does not end with 'Tools'. Using full lowercase name for module.")
    return tool_class_name.lower()


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

            # --- Transform Tools Config --- #
            formatted_tool_configs = []
            if agent_orm.tools and isinstance(agent_orm.tools, list):
                logger.info(f"Agent {agent_id}: Found {len(agent_orm.tools)} tool configurations.")
                for tool_data in agent_orm.tools:
                    if isinstance(tool_data, dict):
                        tool_name = tool_data.get('name') # e.g., "GithubTools"
                        tool_params = tool_data.get('config', {}) # Params for the toolkit's __init__
                        
                        if not tool_name:
                            logger.warning(f"Agent {agent_id}: Skipping tool config due to missing 'name': {tool_data}")
                            continue
                        
                        try:
                            module_name = _tool_name_to_module_name(tool_name)
                            module_path = f"mindloom.tools.{module_name}"
                            formatted_tool_configs.append({
                                'module_path': module_path,
                                'class_name': tool_name,
                                'params': tool_params or {} # Ensure params is a dict
                            })
                            logger.debug(f"Agent {agent_id}: Prepared tool config - module={module_path}, class={tool_name}")
                        except Exception as e:
                             logger.error(f"Agent {agent_id}: Error processing tool config for '{tool_name}': {e}", exc_info=True)
                    else:
                        logger.warning(f"Agent {agent_id}: Skipping invalid tool configuration item (not a dict): {tool_data}")
            else:
                 logger.info(f"Agent {agent_id}: No tools configured or 'tools' field is not a list.")
            # --- End Transform Tools Config --- #

            # --- Instantiate Components --- #
            agno_model = None
            agno_tools = []
            agno_knowledge_bases = []
            agno_storage = None

            try:
                # 1. Language Model
                agno_model = self._create_model(agent_orm.llm_config)

                # 1b. Agent-level Embedder (removed - embedder is now created within _create_storage if needed)
                # embedder_instance = self._create_embedder(agent_orm.embedder_config)

                # 2. Tools (using transformed config)
                agno_tools = self._create_tools(formatted_tool_configs) 

                # 3. Knowledge Bases
                # _create_knowledge_bases handles its own embedders internally per bucket
                agno_knowledge_bases = await self._create_knowledge_bases(agent_orm, session)

                # 4. Storage
                # Pass the agent-level embedder instance created above (Removed - embedder instance no longer passed)
                agno_storage = await self._create_storage(
                    agent_orm.storage_config,
                    agent_id, # Pass agent_id
                    session_id, # Pass session_id
                    # embedder=embedder_instance # Removed embedder pass-through
                )

                agent_params = agent_orm.agent_config or {}

                agno_agent = Agent(
                    name=agent_orm.name,
                    agent_id=agent_orm.id,
                    session_id=session_id,

                    model=agno_model,
                    tools=agno_tools,
                    knowledge=agno_knowledge_bases,
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

            except Exception as e:
                logger.error(f"Failed to create Agno agent instance for {agent_id}: {e}", exc_info=True)
                raise

    def _create_model(self, llm_config: Optional[Dict[str, Any]]) -> Optional[Model]: # Updated return type
        """Creates the Agno LLM instance based on llm_config."""
        if not llm_config:
            # Changed from warning to error as model is usually essential
            logger.error("LLM configuration (llm_config) is missing.")
            raise ConfigurationError("LLM configuration is missing.")

        provider = llm_config.get("provider", "azure_openai").lower()
        params = llm_config.get("params", {})

        if provider == "azure_openai":
            # Check API Key
            api_key_env_var = params.get("api_key_env_var", "AZURE_OPENAI_API_KEY")
            api_key = os.getenv(api_key_env_var)
            if not api_key:
                logger.error(f"Azure OpenAI API key environment variable '{api_key_env_var}' is not set.")
                raise ConfigurationError(f"Azure OpenAI API key environment variable '{api_key_env_var}' is not set.")

            # Check Endpoint
            azure_endpoint = params.get("azure_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT"))
            if not azure_endpoint:
                 logger.error("Azure OpenAI endpoint is not configured in llm_config or AZURE_OPENAI_ENDPOINT env var.")
                 raise ConfigurationError("Azure OpenAI endpoint is not configured.")

            # Check Deployment Name
            deployment_name = params.get("deployment_name", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))
            if not deployment_name:
                 logger.error("Azure OpenAI deployment name is not configured in llm_config or AZURE_OPENAI_DEPLOYMENT_NAME env var.")
                 raise ConfigurationError("Azure OpenAI deployment name is not configured.")

            # Check API Version (Optional, but good practice)
            api_version = params.get("api_version", os.getenv("AZURE_OPENAI_API_VERSION"))
            if not api_version:
                 # If API version becomes strictly required by Agno/Azure, change this to raise ConfigurationError
                 logger.warning("Azure OpenAI API version is not configured in llm_config or AZURE_OPENAI_API_VERSION env var. Proceeding without it.")

            model_params = {
                "api_key": api_key,
                "azure_endpoint": azure_endpoint,
                "azure_deployment": deployment_name,
                "api_version": api_version,
                # Allow overriding model name if specified in params
                "model": params.get("model_name"), # Pass None if not specified, AzureOpenAI might have a default
                # Add other relevant AzureOpenAI params from llm_config['params'] if needed
                # e.g., "temperature": params.get("temperature", 0.7)
            }
            # Remove None values as constructor might not handle them
            model_params = {k: v for k, v in model_params.items() if v is not None}

            try:
                 logger.info(f"Instantiating AzureOpenAI model with endpoint: {azure_endpoint}, deployment: {deployment_name}")
                 return AzureOpenAI(**model_params)
            except Exception as e:
                 logger.error(f"Failed to instantiate AzureOpenAI model: {e}", exc_info=True)
                 # Wrap instantiation errors
                 raise ModelCreationError(f"Failed to instantiate AzureOpenAI model: {e}") from e
        elif provider == "openai":
            api_key = params.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not set for OpenAI model provider.")
                raise ConfigurationError("OPENAI_API_KEY environment variable not set.")

            model_name = params.get("model_name", "gpt-4o")
            model_params = {
                "api_key": api_key,
                "id": model_name, # Changed key from model to id based on Agno example
                **params.get("config_overrides", {})
            }

            try:
                return OpenAI(**model_params)
            except Exception as e:
                logger.error(f"Failed to instantiate OpenAI model: {e}", exc_info=True)
                raise ModelCreationError(f"Failed to instantiate OpenAI model: {e}") from e
        # Add elif for other providers here if needed in the future
        # elif provider == "openai": ...
        else:
            logger.error(f"Unsupported LLM provider specified: {provider}")
            raise ConfigurationError(f"Unsupported LLM provider: {provider}")

    def _create_tools(self, tool_configs: Optional[List[Dict[str, Any]]]) -> List[Toolkit]:
        """Dynamically imports and instantiates Toolkit classes based on names and config from DB."""
        tools_list: List[Toolkit] = []
        if not tool_configs:
            logger.info("No tool configurations provided for agent.")
            return tools_list

        for config in tool_configs:
            class_name = config.get("class_name")
            module_path = config.get("module_path")
            params = config.get("params", {})

            if not class_name or not module_path:
                logger.warning(f"Skipping tool config due to missing 'class_name' or 'module_path': {config}")
                continue

            try:
                logger.info(f"Loading tool: {class_name} from {module_path}")
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)

                # --- Validation Step --- #
                if not inspect.isclass(tool_class) or not issubclass(tool_class, Toolkit):
                    logger.error(f"Configuration Error: Loaded class '{class_name}' from '{module_path}' is not a subclass of agno.tools.toolkit.Toolkit.")
                    raise ConfigurationError(f"Tool class '{class_name}' is not a valid Toolkit subclass.")
                # --- End Validation --- #

                # Instantiate the toolkit with its parameters
                try:
                    tool_instance = tool_class(**params)
                except TypeError as te:
                    # Catch errors where params don't match the tool's __init__ signature
                    logger.error(f"Configuration Error instantiating tool '{class_name}': Parameters {list(params.keys())} likely do not match constructor. Error: {te}", exc_info=True)
                    raise ConfigurationError(f"Invalid parameters provided for tool '{class_name}': {te}") from te
                except Exception as e:
                    # Catch other potential instantiation errors
                    logger.error(f"Error instantiating tool '{class_name}' with params {params}: {e}", exc_info=True)
                    raise ToolCreationError(f"Failed to instantiate tool '{class_name}' after loading: {e}") from e
                    
                tools_list.append(tool_instance)
                logger.info(f"Successfully instantiated tool: {class_name}")

            except ImportError:
                logger.error(f"Failed to import module '{module_path}' for tool '{class_name}'. Check module path.")
                # Optionally re-raise as ToolCreationError or ConfigurationError
                raise ToolCreationError(f"Could not import module '{module_path}' for tool '{class_name}'.")
            except AttributeError:
                logger.error(f"Class '{class_name}' not found in module '{module_path}'. Check class name.")
                # Optionally re-raise as ToolCreationError or ConfigurationError
                raise ToolCreationError(f"Class '{class_name}' not found in module '{module_path}'.")
            except ConfigurationError: # Re-raise validation or TypeError errors
                 raise
            except Exception as e:
                logger.error(f"Failed to instantiate tool '{class_name}' from '{module_path}': {e}", exc_info=True)
                # Optionally re-raise as ToolCreationError
                raise ToolCreationError(f"Failed to instantiate tool '{class_name}': {e}")

        return tools_list

    # --- Knowledge Base Creation Helpers --- #

    def _create_kb_embedder(self, embedder_config: Dict[str, Any]) -> Optional[Embedder]:
        """Creates the Agno Embedder instance based on knowledge base embedder_config."""
        if not embedder_config or not isinstance(embedder_config, dict):
            logger.warning("Knowledge base embedder config is missing or invalid. Cannot create embedder.")
            return None
        
        provider = embedder_config.get("provider")
        model_id = embedder_config.get("model_id")
        api_key_env_var = embedder_config.get("api_key_env_var")
        config_overrides = embedder_config.get("config_overrides", {})
        
        logger.info(f"Creating knowledge base embedder with provider: {provider}, model: {model_id}")
        
        embedder = None
        try:
            if provider == "OpenAIEmbedder" or provider == "OpenAI":
                api_key = os.getenv(api_key_env_var) if api_key_env_var else None
                if not api_key:
                    logger.warning(f"OpenAI API key env var '{api_key_env_var}' not set or empty for KB embedder. Embedder may fail.")
                    # Proceeding allows for potential global key usage within Agno, but log clearly
                embedder = OpenAIEmbedder(api_key=api_key, model=model_id, **config_overrides)
            
            elif provider == "AzureOpenAIEmbedder":
                # Use helper for Azure setup (from settings)
                azure_config = self._get_azure_config(config_overrides) # Reuse Azure config helper
                if not model_id:
                     raise ConfigurationError("Azure KB Embedder requires 'model_id' (deployment name) in embedder_config.")
                embedder = AzureOpenAIEmbedder(
                    api_key=azure_config['api_key'],
                    azure_endpoint=azure_config['endpoint'],
                    deployment_name=model_id, # Azure uses deployment_name for model_id
                    api_version=azure_config['api_version'],
                    **config_overrides
                )
            
            # Add other embedder providers here (e.g., HuggingFace, Cohere)
            elif provider:
                logger.error(f"Unsupported knowledge base embedder provider: {provider}")
                raise ConfigurationError(f"Unsupported KB embedder provider: {provider}")
            else:
                 logger.warning("Knowledge base embedder provider not specified in config.")
        
        except ConfigurationError as ce:
            logger.error(f"Configuration error creating KB embedder: {ce}")
            raise # Re-raise specific configuration errors
        except Exception as e:
            logger.error(f"Unexpected error creating KB embedder ({provider}, {model_id}): {e}", exc_info=True)
            raise EmbedderCreationError(f"Failed to create KB embedder {provider}: {e}") from e
            
        logger.info(f"Successfully created knowledge base embedder instance: {type(embedder).__name__ if embedder else 'None'}")
        return embedder

    def _create_kb_vector_store(self, vector_db_config: Dict[str, Any], bucket_id: uuid.UUID) -> Optional[VectorDb]:
        """Creates the Agno VectorDb instance based on knowledge base vector_db_config."""
        if not vector_db_config or not isinstance(vector_db_config, dict):
            logger.warning(f"Knowledge base vector DB config for bucket {bucket_id} is missing or invalid. Cannot create vector store.")
            return None

        provider = vector_db_config.get("provider")
        config_overrides = vector_db_config.get("config_overrides", {})
        
        logger.info(f"Creating knowledge base vector store for bucket {bucket_id} with provider: {provider}")
        
        vector_store = None
        try:
            if provider == "ChromaDb":
                # Chroma requires path or host/port, handle config variations
                path = config_overrides.get("path", f"./chroma_kb_{bucket_id.hex}") # Default local path
                host = config_overrides.get("host")
                port = config_overrides.get("port")
                collection_name = config_overrides.get("collection_name", f"kb_{bucket_id.hex}")
                
                if host and port:
                     vector_store = ChromaDb(collection_name=collection_name, host=host, port=port, **config_overrides)
                else:
                     vector_store = ChromaDb(collection_name=collection_name, path=path, **config_overrides)
            
            elif provider == "PgVector":
                db_url = self.app_settings.DATABASE_URL # Get DB URL from settings
                if not db_url:
                     raise ConfigurationError("DATABASE_URL setting is not configured. Required for PgVector.")
                table_name = config_overrides.get("table_name", f"kb_{bucket_id.hex}") # Unique table per bucket
                # Ensure embedder dimensions are passed if needed by PgVector constructor (might vary by Agno version)
                vector_store = PgVector(table_name=table_name, db_url=db_url, **config_overrides)
                logger.info(f"PgVector configured for table '{table_name}'")
            
            # Add other vector store providers here
            elif provider:
                logger.error(f"Unsupported knowledge base vector store provider: {provider}")
                raise ConfigurationError(f"Unsupported KB vector store provider: {provider}")
            else:
                 logger.warning(f"Knowledge base vector store provider not specified in config for bucket {bucket_id}.")

        except ConfigurationError as ce:
             logger.error(f"Configuration error creating KB vector store for bucket {bucket_id}: {ce}")
             raise
        except Exception as e:
            logger.error(f"Unexpected error creating KB vector store ({provider}) for bucket {bucket_id}: {e}", exc_info=True)
            raise VectorStoreCreationError(f"Failed to create KB vector store {provider} for bucket {bucket_id}: {e}") from e
            
        logger.info(f"Successfully created knowledge base vector store instance for bucket {bucket_id}: {type(vector_store).__name__ if vector_store else 'None'}")
        return vector_store

    # --- End Knowledge Base Creation Helpers --- #

    async def _create_knowledge_bases(self, agent_orm: AgentORM, db: AsyncSession) -> List[TextKnowledgeBase]:
        """
        Dynamically instantiates KnowledgeBase objects for each linked Content Bucket,
        configures them with embedders and vector stores, and loads content (e.g., from S3).
        """
        logger.info(f"Agent {agent_orm.id}: Starting knowledge base creation for {len(agent_orm.content_buckets)} linked buckets.")
        created_knowledge_bases: List[TextKnowledgeBase] = []

        if not agent_orm.content_buckets:
            logger.info(f"Agent {agent_orm.id}: No content buckets linked. No knowledge bases to create.")
            return []

        # Fetch related buckets if not already loaded (depends on relationship loading strategy)
        # Assuming agent_orm.content_buckets contains loaded ContentBucketORM instances
        
        for bucket_orm in agent_orm.content_buckets:
            bucket_id = bucket_orm.id
            logger.info(f"Agent {agent_orm.id}: Processing Content Bucket ID: {bucket_id}, Name: '{bucket_orm.name}', Type: '{bucket_orm.bucket_type}'")

            knowledge_base = None
            try:
                # 1. Create Embedder for this bucket
                embedder = self._create_kb_embedder(bucket_orm.embedder_config)
                if not embedder:
                    logger.error(f"Agent {agent_orm.id}, Bucket {bucket_id}: Skipping KB creation due to failed embedder setup.")
                    continue # Skip this bucket if embedder fails

                # 2. Create Vector Store for this bucket
                vector_store = self._create_kb_vector_store(bucket_orm.vector_db_config, bucket_id)
                if not vector_store:
                    logger.error(f"Agent {agent_orm.id}, Bucket {bucket_id}: Skipping KB creation due to failed vector store setup.")
                    continue # Skip this bucket if vector store fails

                # 3. Instantiate and Load Knowledge Base based on type
                if bucket_orm.bucket_type == 'S3':
                    s3_config = bucket_orm.config
                    if not isinstance(s3_config, dict):
                        raise ConfigurationError(f"Bucket {bucket_id}: S3 'config' must be a dictionary.")
                    
                    bucket_name = s3_config.get('bucket_name')
                    prefix = s3_config.get('prefix') # Directory path in S3
                    
                    if not bucket_name or not prefix:
                        raise ConfigurationError(f"Bucket {bucket_id}: S3 config missing required keys 'bucket_name' or 'prefix'. Found: {s3_config.keys()}")
                    
                    logger.info(f"Agent {agent_orm.id}, Bucket {bucket_id}: Instantiating S3PDFKnowledgeBase for s3://{bucket_name}/{prefix}")
                    # TODO: Confirm if S3PDFKnowledgeBase requires AWS credentials setup (e.g., boto3) or if Agno handles it.
                    # Assuming Agno handles credential chain (env vars, config files, IAM roles)
                    knowledge_base = S3PDFKnowledgeBase(
                        bucket_name=bucket_name,
                        key=prefix, # Agno S3PDFKnowledgeBase might use 'key' for prefix
                        vector_db=vector_store,
                        embedder=embedder,
                        # Pass other relevant params from s3_config if needed by S3PDFKnowledgeBase constructor
                    )
                    
                    # Load documents from S3 - Agno handles download, parse, embed, store
                    logger.info(f"Agent {agent_orm.id}, Bucket {bucket_id}: Calling knowledge_base.load() to sync S3 content.")
                    # Use recreate=False to avoid reprocessing unchanged files unless specified otherwise
                    recreate_flag = s3_config.get("recreate_on_load", False) 
                    knowledge_base.load(recreate=recreate_flag)
                    logger.info(f"Agent {agent_orm.id}, Bucket {bucket_id}: S3 load process initiated.")
                
                # TODO: Add handlers for other bucket_types (e.g., 'Local', 'URL')
                # elif bucket_orm.bucket_type == 'Local': ...
                
                else:
                    logger.warning(f"Agent {agent_orm.id}, Bucket {bucket_id}: Unsupported bucket_type '{bucket_orm.bucket_type}'. Cannot create knowledge base.")

                if knowledge_base:
                    created_knowledge_bases.append(knowledge_base)
                    logger.info(f"Agent {agent_orm.id}, Bucket {bucket_id}: Successfully created and initiated load for Knowledge Base: {type(knowledge_base).__name__}")
            
            except (ConfigurationError, EmbedderCreationError, VectorStoreCreationError) as specific_error:
                # Log specific configuration/creation errors and continue to next bucket
                logger.error(f"Agent {agent_orm.id}: Failed to create knowledge base for Bucket {bucket_id} due to error: {specific_error}")
            except Exception as e:
                # Catch-all for unexpected errors during KB creation/loading for a specific bucket
                logger.error(f"Agent {agent_orm.id}: Unexpected error processing Bucket {bucket_id}: {e}", exc_info=True)
                # Decide whether to continue to next bucket or raise

        logger.info(f"Agent {agent_orm.id}: Finished knowledge base creation. Instantiated {len(created_knowledge_bases)} knowledge bases.")
        return created_knowledge_bases


    def _create_embedder(self, embedder_config: Optional[Dict[str, Any]]) -> Optional[Embedder]: # Keep this for agent/team level embedder if needed
        """Creates the Agno Embedder instance based on agent/team-level embedder_config."""
        if not embedder_config:
            # Changed from warning to error as model is usually essential
            logger.error("Embedder configuration (embedder_config) is missing.")
            raise ConfigurationError("Embedder configuration is missing.")

        provider = embedder_config.get("provider", "azure_openai").lower()
        params = embedder_config.get("params", {})

        if provider == "azure_openai":
            # Check API Key
            api_key_env_var = params.get("api_key_env_var", "AZURE_OPENAI_API_KEY")
            api_key = os.getenv(api_key_env_var)
            if not api_key:
                logger.error(f"Azure OpenAI API key environment variable '{api_key_env_var}' is not set.")
                raise ConfigurationError(f"Azure OpenAI API key environment variable '{api_key_env_var}' is not set.")

            # Check Endpoint
            azure_endpoint = params.get("azure_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT"))
            if not azure_endpoint:
                 logger.error("Azure OpenAI endpoint is not configured in embedder_config or AZURE_OPENAI_ENDPOINT env var.")
                 raise ConfigurationError("Azure OpenAI endpoint is not configured.")

            # Check Deployment Name
            deployment_name = params.get("deployment_name", os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"))
            if not deployment_name:
                 logger.error("Azure OpenAI embedding deployment name is not configured in embedder_config or AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME env var.")
                 raise ConfigurationError("Azure OpenAI embedding deployment name is not configured.")

            # Check API Version (Optional, but good practice)
            api_version = params.get("api_version", os.getenv("AZURE_OPENAI_API_VERSION"))
            if not api_version:
                 logger.warning("Azure OpenAI API version is not configured in embedder_config or AZURE_OPENAI_API_VERSION env var. Proceeding without it.")

            embedder_params = {
                "api_key": api_key,
                "azure_endpoint": azure_endpoint,
                "azure_deployment": deployment_name,
                "api_version": api_version,
                # Allow overriding model name if specified in params
                "model": params.get("model_name"), # Pass None if not specified, AzureOpenAI might have a default
                # Add other relevant AzureOpenAIEmbedder params from embedder_config['params'] if needed
                # e.g., "temperature": params.get("temperature", 0.7)
            }
            # Remove None values as constructor might not handle them
            embedder_params = {k: v for k, v in embedder_params.items() if v is not None}

            try:
                 logger.info(f"Instantiating AzureOpenAIEmbedder with endpoint: {azure_endpoint}, deployment: {deployment_name}")
                 return AzureOpenAIEmbedder(**embedder_params)
            except Exception as e:
                 logger.error(f"Failed to instantiate AzureOpenAIEmbedder: {e}", exc_info=True)
                 # Wrap instantiation errors
                 raise KnowledgeCreationError(f"Failed to instantiate AzureOpenAIEmbedder: {e}") from e
        elif provider == "openai":
            api_key = params.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not set for OpenAI embedder provider.")
                raise ConfigurationError("OPENAI_API_KEY environment variable not set for embedder.")

            embedder_params = {
                "api_key": api_key,
                **params.get("config_overrides", {})
            }

            try:
                return OpenAIEmbedder(**embedder_params)
            except Exception as e:
                logger.error(f"Failed to instantiate OpenAIEmbedder: {e}", exc_info=True)
                raise KnowledgeCreationError(f"Failed to instantiate OpenAIEmbedder: {e}") from e
        # Add elif for other providers here if needed in the future
        # elif provider == "openai": ...
        else:
            logger.error(f"Unsupported embedder provider specified: {provider}")
            raise ConfigurationError(f"Unsupported embedder provider: {provider}")

    async def _create_storage(
        self,
        storage_config: Optional[Dict[str, Any]],
        agent_id: uuid.UUID,
        session_id: uuid.UUID,
        # embedder: Optional[Embedder] = None # Removed argument
    ):
         """Creates the Agno Storage instance based on storage_config."""
         if not storage_config:
             # Default to Postgres if no config specified
             logger.info(f"Agent {agent_id}: No storage config provided, defaulting to PostgresStorage.")
 
             # Get necessary async engine for run_sync
             db_engine = get_async_db_engine()
 
             # Get default settings
             default_db_url = str(self.app_settings.DATABASE_URL)
             default_table_name = "agent_sessions" # Default table name as per example
 
             if not default_db_url:
                 raise ConfigurationError(f"Agent {agent_id}: Default Database URL is required for PostgresStorage but not found in settings.")
 
             # Define sync instantiation function using db_url and table_name
             def _sync_instantiate_postgres():
                 return PostgresStorage(
                     db_url=default_db_url,
                     table_name=default_table_name
                     # Note: agent_id/session_id are not params of PostgresStorage.__init__
                 )
 
             try:
                 # Run synchronous instantiation using run_sync
                 async with db_engine.connect() as conn:
                     storage_instance = await conn.run_sync(_sync_instantiate_postgres)
                 return storage_instance
             except Exception as e:
                 logger.exception(f"Agent {agent_id}: Failed during run_sync instantiation of default PostgresStorage: {e}")
                 raise StorageCreationError(f"Agent {agent_id}: Failed to instantiate default Postgres storage via run_sync.") from e
 
         storage_type = storage_config.get("type")
         params = storage_config.get("params", {})
         logger.info(f"Agent {agent_id}: Creating storage of type '{storage_type}' with params: {params}")
 
         try:
             if storage_type == "PostgresAgentStorage":
                 # Get necessary async engine for run_sync
                 db_engine = get_async_db_engine()
 
                 # --- Corrected to use PostgresStorage with run_sync and db_url/table_name --- #
                 db_url = params.get("db_url", str(self.app_settings.DATABASE_URL))
                 table_name = params.get("table_name", "agent_sessions") # Default table name
 
                 if not db_url:
                     raise ConfigurationError(f"Agent {agent_id}: 'db_url' is required for PostgresStorage but not found in params or settings.")
 
                 # Define sync instantiation function using db_url and table_name
                 def _sync_instantiate_postgres():
                     # Exclude db_url and table_name from extra params if they exist
                     extra_params = {k: v for k, v in params.items() if k not in ["db_url", "table_name"]}
                     return PostgresStorage(
                         db_url=db_url,
                         table_name=table_name,
                         **extra_params # Pass remaining params
                     )
 
                 try:
                     # Run synchronous instantiation using run_sync
                     async with db_engine.connect() as conn:
                         storage_instance = await conn.run_sync(_sync_instantiate_postgres)
                     return storage_instance
                 except Exception as e:
                     logger.exception(f"Agent {agent_id}: Failed during run_sync instantiation of PostgresStorage '{storage_type}': {e}")
                     raise StorageCreationError(f"Agent {agent_id}: Failed to instantiate storage type '{storage_type}' via run_sync.") from e
                 # --- End Correction --- #
 
             elif storage_type == "RedisMemoryDb":
                 try:
                     redis_url = params.get("redis_url", self.app_settings.REDIS_URL)
                 except Exception as e:
                     logger.error(f"Agent {agent_id}: Failed to instantiate RedisMemoryDb: {e}", exc_info=True)
                     raise StorageCreationError(f"Agent {agent_id}: Failed to instantiate RedisMemoryDb: {e}") from e
 
                 # --> Added: Get embedder config from storage params
                 embedder_config = params.get("embedder_config")
                 if not embedder_config or not isinstance(embedder_config, dict):
                     raise ConfigurationError(f"Agent {agent_id}: 'embedder_config' dictionary is required within storage_config params for RedisMemoryDb.")
 
                 # --> Added: Create embedder instance using the config
                 embedder = self._create_embedder(embedder_config)
                 if not embedder:
                     # _create_embedder logs specific errors, raise general one here
                     raise StorageCreationError(f"Agent {agent_id}: Failed to create embedder instance required for RedisMemoryDb.")
                 # <-- End Added
 
                 # Construct a unique session ID for this specific agent run
                 redis_session_key = params.get("session_id_key_template", "agent:{agent_id}:run:{session_id}:memory")
                 redis_session_key = redis_session_key.format(agent_id=agent_id, session_id=session_id)
 
                 logger.debug(f"Agent {agent_id}: Using Redis session key: {redis_session_key}")
                 return RedisMemoryDb(
                     redis_url=redis_url,
                     session_id=redis_session_key, # Use the constructed key
                     embedder=embedder # Pass the embedder instance
                     # Add other RedisMemoryDb specific params if needed from 'params'
                 )
             else:
                 raise ConfigurationError(f"Agent {agent_id}: Unsupported storage type specified: {storage_type}")
         except ConfigurationError as e:
              logger.error(f"Agent {agent_id}: Configuration error creating storage: {e}")
              raise # Re-raise specific configuration errors
         except Exception as e:
             logger.error(f"Agent {agent_id}: Failed to instantiate storage type '{storage_type}': {e}", exc_info=True)
             # Wrap general errors in StorageCreationError
             raise StorageCreationError(f"Agent {agent_id}: Failed to instantiate storage type '{storage_type}': {e}") from e