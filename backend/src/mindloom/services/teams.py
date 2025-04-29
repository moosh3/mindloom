# In backend/src/mindloom/services/teams.py
import uuid
import asyncio
import logging
import os
from typing import List, Optional, Dict, Any, TYPE_CHECKING
import agno
from agno.memory.team import TeamMemory as AgnoMemory
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.db.redis import RedisMemoryDb # <-- Import RedisMemory

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
    ServiceError
)

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
            logger.info("No embedder configuration found in team's knowledge_config.")
            return None
        # ... (Implementation similar to AgentService._create_embedder) ...
        # For brevity, assuming AzureOpenAIEmbedder setup here
        embedder_conf = knowledge_config['embedder']
        provider = embedder_conf.get("provider", "azure_openai")
        params = embedder_conf.get("params", {})
        if provider.lower() == "azure_openai":
            api_key = os.getenv(params.get("api_key_env_var"))
            embedder_params = {
                "api_key": api_key,
                "azure_endpoint": params.get("azure_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT")),
                "api_version": params.get("api_version", os.getenv("AZURE_OPENAI_API_VERSION")),
                "azure_deployment": params.get("deployment_name", os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")),
            }
            embedder_params = {k: v for k, v in embedder_params.items() if v is not None}
            try:
                return AzureOpenAIEmbedder(**embedder_params)
            except Exception as e:
                logger.error(f"Failed to instantiate team AzureOpenAIEmbedder: {e}")
                return None
        else:
             logger.warning(f"Unsupported team embedder provider: {provider}")
             return None

    def _create_team_knowledge(self, team_orm: TeamORM) -> Optional['VectorStore']:
        """Creates the Agno Knowledge Base instance for the team (no dynamic loading yet)."""
        if not team_orm.knowledge_config:
            logger.info(f"Team {team_orm.id}: No knowledge_config provided.")
            return None
        
        embedder = self._create_team_embedder(team_orm.knowledge_config)
        if not embedder:
             logger.error(f"Team {team_orm.id}: Cannot create knowledge base without embedder.")
             raise KnowledgeCreationError(f"Team {team_orm.id}: Cannot create knowledge base without embedder.")

        vector_store_config = team_orm.knowledge_config.get("vector_store", {})
        # Use team ID for table name to avoid conflicts
        table_name = vector_store_config.get("table_name_prefix", "team_knowledge") + f"_{str(team_orm.id).replace('-', '_')}"
        connection_string = vector_store_config.get("connection_string", settings.DATABASE_URL_PSYCOPG)

        try:
            # Assuming PgVector is the desired store type for teams too
            vector_store = PgVector(
                connection_string=connection_string,
                embedding_function=embedder,
                collection_name=table_name,
                # Add other PgVector specific params if needed
            )
            logger.info(f"Team {team_orm.id}: Initialized PgVector store '{table_name}'.")
            # Note: No dynamic loading from S3/Content Buckets is implemented here yet.
            # The store will be empty unless pre-populated externally or config changes.
            return vector_store
        except Exception as e:
            logger.error(f"Team {team_orm.id}: Failed to instantiate PgVector store '{table_name}': {e}")
            raise KnowledgeCreationError(f"Team {team_orm.id}: Failed to instantiate PgVector store '{table_name}': {e}")

    def _create_team_storage(self, team_orm: TeamORM) -> Optional[AgnoMemory]:
        """Creates the Agno Storage instance for the team. Defaults to RedisMemory if no config is provided."""
        storage_config = team_orm.storage_config or {} # Ensure storage_config is a dict
        storage_type = storage_config.get("type", "RedisMemory") # Default to Redis
        storage_params = storage_config.get("params", {})

        # Construct a unique session ID/prefix for the team's memory
        session_id = storage_params.get("session_id", f"team_memory:{team_orm.id}")
        redis_url = storage_params.get("redis_url", settings.REDIS_URL)

        if storage_type == "RedisMemory":
            if not redis_url:
                logger.error(f"Team {team_orm.id}: Redis URL not configured. Cannot create RedisMemory.")
                raise StorageCreationError(f"Team {team_orm.id}: Redis URL not configured.")
            try:
                logger.info(f"Team {team_orm.id}: Initializing RedisMemory with session_id '{session_id}'.")
                # Pass necessary params like redis_url and session_id
                # Adjust based on RedisMemory's actual __init__ signature
                return RedisMemory(redis_url=redis_url, session_id=session_id)
            except Exception as e:
                logger.error(f"Team {team_orm.id}: Failed to instantiate RedisMemory: {e}")
                raise StorageCreationError(f"Team {team_orm.id}: Failed to instantiate RedisMemory: {e}")

        elif storage_type == "PostgresMemoryDb":
            connection_string = storage_params.get("connection_string", settings.DATABASE_URL_PSYCOPG)
            table_name = storage_params.get("table_name", f"team_memory_{str(team_orm.id).replace('-', '_')}")
            try:
                logger.info(f"Team {team_orm.id}: Initializing PostgresMemoryDb with table '{table_name}'.")
                raise NotImplementedError("PostgresMemoryDb instantiation for Teams needs verification.")
            except Exception as e:
                logger.error(f"Team {team_orm.id}: Failed to instantiate PostgresMemoryDb: {e}")
                raise StorageCreationError(f"Team {team_orm.id}: Failed to instantiate PostgresMemoryDb: {e}")
        else:
            logger.warning(f"Team {team_orm.id}: Unsupported storage type '{storage_type}'. No team memory will be used.")
            return None

    async def create_agno_team_instance(self, team_id: uuid.UUID) -> Optional[Team]:
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

        # --- Instantiate Team Components --- 
        try:
            leader_model = self.agent_service._create_model(team_orm.llm_config)
            # Wrap knowledge/storage creation in try-except as well
            try:
                team_knowledge = self._create_team_knowledge(team_orm)
            except KnowledgeCreationError as kce:
                logger.error(f"Team {team_id}: Failed to create team knowledge: {kce}")
                raise TeamCreationError(f"Failed to create knowledge for team {team_id}: {kce}") from kce
        
            try:
                team_storage = self._create_team_storage(team_orm)
            except StorageCreationError as sce:
                logger.error(f"Team {team_id}: Failed to create team storage: {sce}")
                raise TeamCreationError(f"Failed to create storage for team {team_id}: {sce}") from sce

        except ServiceError as se: # Catch specific service errors from component creation
            logger.error(f"Team {team_id}: Service error creating components: {se}")
            raise TeamCreationError(f"Error creating components for team {team_id}: {se}") from se
        except Exception as e:
            logger.exception(f"Team {team_id}: Unexpected error creating team components: {e}")
            raise TeamCreationError(f"Unexpected error creating components for team {team_id}: {e}") from e

        if not leader_model:
            logger.error(f"Team {team_id}: Leader model creation returned None unexpectedly.")
            raise TeamCreationError(f"Failed to create leader model for team {team_id}. Configuration might be invalid.")

        # Extract direct Team parameters
        team_config_params = team_orm.team_config or {}
        team_mode = team_orm.mode # Should be List[str]

        if not team_mode:
            logger.warning(f"Team {team_id} has no mode defined. Defaulting might be needed or raise error.")
            # team_mode = ["coordinate"] # Example default
            raise TeamCreationError(f"Team {team_id} has no mode defined.")
            # Or raise error - mode is likely essential

        # Prepare memory configuration
        memory_instance = None
        enable_history = False
        history_n = 0

        if team_orm.enable_memory:
            logger.debug(f"Instantiating Agno Memory for team {team_id} with history length {team_orm.history_length}")
            # TODO: Configure Memory with model, summarizer if needed later
            try:
                # Instantiate the persistent database backend for memory
                logger.info(f"Configuring PostgresMemoryDb for team {team_id} (table: mindloom_team_memories)")
                memory_db = PostgresMemoryDb(
                    table_name="mindloom_team_memories",
                    schema="public", # Use public schema
                    db_engine=self.engine # Pass the existing SQLAlchemy engine
                )
                # Initialize Memory with the storage backend
                # Note: We might need to pass a model here if MemoryManager/Summarizer are used later
                memory_instance = AgnoMemory(db=memory_db)
                logger.debug(f"Agno Memory for team {team_id} configured with Postgres backend.")
            except Exception as e:
                logger.exception(f"Failed to instantiate PostgresMemoryDb for team {team_id}: {e}")
                # Decide: fail team creation or proceed with in-memory? For now, fail.
                raise TeamCreationError(f"Failed to configure persistent memory: {e}") from e
            enable_history = True
            history_n = team_orm.history_length

        # --- Prepare Agno Team Constructor Args --- 
        team_constructor_args = {
            "name": team_orm.name,
            "members": member_agents, # List of created Agent instances
            "model": leader_model,
            "mode": team_mode,
            "knowledge": team_knowledge,
            "storage": team_storage,
            "description": team_orm.description,
            "instructions": team_orm.instructions,
            # Map params from team_config_params to Agno Team args
            'show_tool_calls': team_config_params.get('show_tool_calls', True),
            'markdown': team_config_params.get('markdown', False),
            'enable_agentic_context': team_config_params.get('enable_agentic_context', True),
            'share_member_interactions': team_config_params.get('share_member_interactions', True),
            'enable_team_history': enable_history,
            'num_of_interactions_from_history': history_n,
            'enable_agentic_memory': team_config_params.get('enable_agentic_memory', True),
            'show_members_responses': team_config_params.get('show_members_responses', True),
            # Add any other direct params Agno Team constructor accepts
            "memory": memory_instance # Pass the instantiated memory object (or None)
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