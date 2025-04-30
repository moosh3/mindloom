import os
import sys
import uuid
import json
from datetime import datetime
import asyncio
from typing import Dict, Any, Optional, Union
import logging

# SQLAlchemy Imports
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

# Mindloom Model & Service Imports
from mindloom.app.models.run import RunORM, RunStatus
from mindloom.services.agents import AgentService
from mindloom.services.teams import TeamService
# Import Agno Agent/Team classes
from agno.agent import Agent as AgnoAgent
from agno.team.team import Team as AgnoTeam
# Import service exceptions for specific handling
from mindloom.services.exceptions import (
    TeamCreationError,
    AgentCreationError,
    KnowledgeCreationError,
    StorageCreationError,
    ServiceError
)

# Import the Redis service for publishing logs
import mindloom.services.redis as redis_service

# Import settings
from mindloom.core.config import settings

# Import DB setup functions
from mindloom.db.session import get_async_db_session, async_session_maker

# --- Logging Setup ---
logger = logging.getLogger("run_executor")
logger.setLevel(logging.INFO)
# Basic console handler for stdout/stderr (Kubernetes logs)
stream_handler = logging.StreamHandler(sys.stdout)
# Updated formatter to include run_id
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(run_id)s] %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# --- End Logging Setup ---

# --- Redis Logging Handler ---
class RedisPubSubHandler(logging.Handler):
    """
    A logging handler that publishes log records to a Redis Pub/Sub channel.
    Uses asyncio.create_task for non-blocking publishing.
    """
    def __init__(self, run_id: uuid.UUID, level=logging.NOTSET):
        super().__init__(level=level)
        self.run_id = run_id
        self.channel_name = f"run_logs:{self.run_id}"
        # Assumes redis_service.initialize_async() was called successfully before instantiation.

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record into a JSON string."""
        log_data = {
            "timestamp": record.created, # epoch float
            "level": record.levelname,
            "message": record.getMessage(), # Get formatted message
            "name": record.name,
            "run_id": str(self.run_id),
        }
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
             log_data["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_data)

    def emit(self, record: logging.LogRecord):
        """Formats the record and publishes it asynchronously to the Redis channel."""
        try:
            message_payload = self.format(record)
            # Fire-and-forget publish task
            asyncio.create_task(self._publish_message(message_payload))
        except Exception:
            self.handleError(record) # Log internal handler errors safely

    async def _publish_message(self, message: str):
        """Helper coroutine to publish the message via redis_service."""
        try:
            # Publish using the shared redis_service client
            if redis_service.client:
                 await redis_service.publish(self.channel_name, message)
            else:
                 # Fallback to stderr if redis client is gone somehow
                 print(f"Redis client not available for handler. Log not published via PubSub: {message[:100]}...", file=sys.stderr)
        except Exception as e:
            # Log publishing errors to stderr to avoid loops if logger uses this handler
            print(f"Error publishing log message to Redis channel {self.channel_name}: {e}", file=sys.stderr)

    def close(self): # Implement close method
        # Usually used to close resources, but redis connection is shared via service
        # So, just call the parent's close
        super().close()
# --- End Redis Logging Handler ---

logger.info("Initializing Mindloom Run Executor...", extra={"run_id": "PENDING_VALIDATION"})

async def main():
    """Main execution logic for the run executor."""
    run_id_str = os.getenv("RUN_ID")
    runnable_id_str = os.getenv("RUNNABLE_ID")
    runnable_type = os.getenv("RUNNABLE_TYPE")
    input_data_json = os.getenv("INPUT_DATA_JSON", "{}") # Default to empty dict

    run_id: Optional[uuid.UUID] = None
    redis_handler: Optional[RedisPubSubHandler] = None
    engine = None
    async_session_factory = None
    final_status: RunStatus = RunStatus.FAILED # Default to FAILED
    initial_log_extra = {"run_id": run_id_str or "UNKNOWN"}
    log_extra = initial_log_extra # Will be updated once run_id is validated

    try:
        # --- Initial Validation and Setup ---
        if not all([run_id_str, runnable_id_str, runnable_type]):
            raise ValueError("Missing required environment variables: RUN_ID, RUNNABLE_ID, RUNNABLE_TYPE")

        run_id = uuid.UUID(run_id_str)
        runnable_id = uuid.UUID(runnable_id_str)
        log_extra = {"run_id": str(run_id)} # Update log extra with validated UUID
        logger.info(f"Processing Run ID: {run_id}", extra=log_extra)

        input_data = json.loads(input_data_json)
        if not isinstance(input_data, dict):
            # Agno run expects a dict input, often {"input": "user query"}
            input_data = {"input": str(input_data)} # Basic wrapping if not dict
            logger.warning(f"Input data was not a dictionary, wrapped as {{'input': ...}}", extra=log_extra)

        if runnable_type not in ['agent', 'team']:
            raise ValueError(f"Invalid RUNNABLE_TYPE: {runnable_type}. Must be 'agent' or 'team'.")

        # --- Initialize Services & DB ---
        # Initialize Redis (important for the handler)
        await redis_service.initialize_async()
        if not redis_service.client:
             raise ConnectionError("Failed to initialize Redis connection for logging.")
        logger.info("Redis connection initialized.", extra=log_extra)

        # Create Redis Handler and add to logger
        redis_handler = RedisPubSubHandler(run_id=run_id)
        logger.addHandler(redis_handler)
        logger.info("RedisPubSubHandler added to logger.", extra=log_extra)

        # Use the imported async_session_maker directly
        # It's already been configured with the engine from session.py
        async_session_factory = async_session_maker
        logger.info("Database engine and session factory initialized.", extra=log_extra)

        # --- Fetch Run and Update Status to RUNNING ---
        async with async_session_factory() as session:
            run = await session.get(RunORM, run_id)
            if not run:
                raise LookupError(f"Run with ID {run_id} not found in the database.")

            run.status = RunStatus.RUNNING
            run.started_at = datetime.utcnow()
            session.add(run)
            await session.commit()
            logger.info("Run status updated to RUNNING in database.", extra=log_extra)

        # --- Instantiate and Execute Agent/Team ---
        agno_runnable: Optional[Union[AgnoAgent, AgnoTeam]] = None
        final_output: Optional[Dict] = None # Initialize final_output
        aggregated_response: Optional[Union[RunResponse, TeamRunResponse]] = None # To hold the last chunk
        results_channel = f"run_results:{run_id_str}" # Define channel for result chunks

        try:
            # Get a single database session for the entire agent/team instantiation and execution
            async with async_session_factory() as session:
                # Instantiate the appropriate service and create the runnable instance
                logger.info(f"Attempting to instantiate {runnable_type} with ID: {runnable_id}", extra=log_extra)

                if runnable_type == 'agent':
                    agent_service = AgentService(db=session)
                    logger.info("AgentService initialized.", extra=log_extra)
                    agno_runnable = await agent_service.create_agno_agent_instance(
                        agent_id=runnable_id,
                        session_id=run_id  # Pass run_id as session_id context
                    )
                    logger.info(f"Agent {runnable_id} instantiated successfully.", extra=log_extra)

                elif runnable_type == 'team':
                    team_service = TeamService(db=session)
                    logger.info("TeamService initialized.", extra=log_extra)
                    agno_runnable = await team_service.create_agno_team_instance(
                        team_id=runnable_id,
                        session_id=run_id  # Pass run_id as session_id context
                    )
                    logger.info(f"Team {runnable_id} instantiated successfully.", extra=log_extra)

            if not agno_runnable:
                 # Should be caught by service exceptions below, but defensive check
                 raise ValueError(f"Failed to instantiate {runnable_type} {runnable_id}. Instance is None.")

            # Execute the run using the async stream
            logger.info(f"Starting streaming run for {runnable_type} {runnable_id}...", extra=log_extra)

            async for chunk in agno_runnable.arun(input=input_data, handlers=[redis_handler], stream=True):
                # Process each chunk (e.g., log, potentially publish to another channel)
                logger.debug(f"Received stream chunk: {type(chunk)}", extra=log_extra)
                if isinstance(chunk, (RunResponse, TeamRunResponse)):
                    aggregated_response = chunk # Store the latest complete response object

                    # Publish the chunk to the results channel
                    try:
                        chunk_json = chunk.model_dump_json() # Use Pydantic v2 serialization
                        await redis_service.publish(results_channel, chunk_json)
                        logger.debug(f"Published chunk to {results_channel}: {chunk_json}", extra=log_extra)
                    except AttributeError:
                        # Fallback for older Pydantic or different object types
                        try:
                            chunk_dict = chunk.dict() # Pydantic v1
                            chunk_json = json.dumps(chunk_dict)
                            await redis_service.publish(results_channel, chunk_json)
                            logger.debug(f"Published chunk (dict) to {results_channel}", extra=log_extra)
                        except Exception as pub_err:
                            logger.warning(f"Failed to serialize/publish chunk to Redis {results_channel}: {pub_err}", extra=log_extra)
                    except Exception as pub_err:
                        logger.warning(f"Failed to publish chunk to Redis {results_channel}: {pub_err}", extra=log_extra)
                else:
                    logger.warning(f"Received unexpected chunk type: {type(chunk)}", extra=log_extra)

        except (AgentCreationError, TeamCreationError, KnowledgeCreationError, StorageCreationError, ServiceError) as creation_err:
            logger.error(f"Failed to instantiate {runnable_type} {runnable_id}: {creation_err}", exc_info=True, extra=log_extra)
            final_status = RunStatus.FAILED
            # Store error in output
            final_output = {"error": f"Instantiation failed: {str(creation_err)}"}
        except RunCancelledException as cancel_err:
            logger.info(f"Run {run_id} was cancelled during execution: {cancel_err}", extra=log_extra)
            final_status = RunStatus.CANCELLED
            final_output = {"error": f"Run cancelled: {str(cancel_err)}"}
        except Exception as run_err:
            logger.error(f"Error during {runnable_type} {runnable_id} streaming execution: {run_err}", exc_info=True, extra=log_extra)
            final_status = RunStatus.FAILED
            final_output = {"error": f"Execution failed: {str(run_err)}"}

        # --- Final Status Update ---
        async with async_session_factory() as session:
            run = await session.get(RunORM, run_id)
            if run:
                logger.info(f"Finalizing Run {run_id} with status {final_status}.", extra=log_extra)
                run.status = final_status
                run.ended_at = datetime.utcnow()

                # Store the aggregated output
                if final_output is not None:
                    try:
                        # Attempt to store as JSON
                        run.output_data = json.loads(json.dumps(final_output)) # Ensure it's valid JSON structure
                    except (TypeError, json.JSONDecodeError) as json_err:
                        logger.warning(f"Output for run {run_id} is not JSON serializable: {json_err}. Storing as error string.", extra=log_extra)
                        run.output_data = {"error": "Output not JSON serializable", "details": str(final_output)}
                        run.status = RunStatus.FAILED # If output failed to serialize, mark run as failed
                    except Exception as ser_err:
                        logger.error(f"Unexpected error serializing output for run {run_id}: {ser_err}", exc_info=True, extra=log_extra)
                        run.output_data = {"error": "Unexpected error serializing output", "details": str(final_output)}
                        run.status = RunStatus.FAILED
                else:
                     run.output_data = {} # Store empty dict if final_output was None

                # Store error message separately if status is FAILED or CANCELLED
                if final_status in [RunStatus.FAILED, RunStatus.CANCELLED] and isinstance(final_output, dict):
                     run.error_message = final_output.get("error", "Unknown error")
                elif final_status == RunStatus.COMPLETED:
                     run.error_message = None # Clear any previous error message on success

                session.add(run)
                try:
                    await session.commit()
                    logger.info(f"Final status {final_status} and output committed to DB for Run {run_id}.", extra=log_extra)
                except Exception as commit_err:
                    logger.error(f"Error committing final status and output for Run {run_id}: {commit_err}", exc_info=True, extra=log_extra)

    except (ValueError, TypeError, json.JSONDecodeError) as setup_parse_err:
        # Catch errors during initial parsing before run_id is reliable UUID
        logger.error(f"FATAL: Error parsing environment variables or initial setup: {setup_parse_err}", extra=initial_log_extra)
        final_status = RunStatus.FAILED # Ensure final status is FAILED for exit code
        sys.exit(1) # Exit on fatal setup errors
    except Exception as setup_e:
        # Catch other unexpected errors during setup before main execution loop
        logger.error(f"FATAL: Unexpected error during setup: {setup_e}", exc_info=True, extra=log_extra if run_id else initial_log_extra)
        final_status = RunStatus.FAILED # Ensure final status is FAILED for exit code
        sys.exit(1) # Exit on fatal setup errors
    finally:
        # Determine the correct extra dict for final logging
        final_log_extra = log_extra if run_id else initial_log_extra
        log_final_status_val = final_status.value if isinstance(final_status, RunStatus) else str(final_status)

        logger.info(f"Mindloom Run Executor finished. Final Status: {log_final_status_val}", extra=final_log_extra)


        # --- Cleanup ---
        # Remove the handler if it was added
        if redis_handler:
            logger.info("Removing RedisPubSubHandler from logger.", extra=final_log_extra)
            logger.removeHandler(redis_handler)
            try:
                 redis_handler.close() # Handlers should have a close method
            except Exception as hc_e:
                 logger.warning(f"Error closing RedisPubSubHandler: {hc_e}", extra=final_log_extra)


        # Close Redis connection ONLY if this executor is the sole manager.
        # Assuming shared state based on redis_service, so we DON'T close here.
        # If this script *owned* the connection, you would close it:
        # if redis_handler: # Only if handler was successfully added (implies Redis was init'd)
        #    await redis_service.close()

        # Dispose DB engine
        if engine:
            logger.info("Disposing database engine.", extra=final_log_extra)
            try:
                 await engine.dispose()
                 logger.info("Database engine disposed.", extra=final_log_extra)
            except Exception as db_disp_e:
                 logger.error(f"Error disposing database engine: {db_disp_e}", extra=final_log_extra)

        # --- End Cleanup ---

        # Exit with appropriate code based on the final determined status
        sys.exit(0 if final_status == RunStatus.COMPLETED else 1)


if __name__ == "__main__":
    asyncio.run(main())
