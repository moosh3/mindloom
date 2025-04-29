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
    # Initial log before run_id is validated as UUID
    logger.info("Starting main execution block...", extra={"run_id": "PENDING_VALIDATION"})

    # 1. Read Environment Variables
    run_id_str = os.getenv("RUN_ID")
    runnable_type = os.getenv("RUNNABLE_TYPE")
    runnable_id_str = os.getenv("RUNNABLE_ID")
    input_data_str = os.getenv("INPUT_DATA", "{}")
    db_url = os.getenv("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL") # Used by services

    # Use run_id_str for logging until run_id (UUID) is confirmed valid
    initial_log_extra = {"run_id": run_id_str or "UNKNOWN"}
    logger.info(f"RUN_ID_STR: {run_id_str}", extra=initial_log_extra)
    logger.info(f"RUNNABLE_TYPE: {runnable_type}", extra=initial_log_extra)
    logger.info(f"RUNNABLE_ID: {runnable_id_str}", extra=initial_log_extra)
    logger.info(f"DATABASE_URL: {'*' * 5 if db_url else 'Not Set'}", extra=initial_log_extra)
    logger.info(f"REDIS_URL: {'*' * 5 if redis_url else 'Not Set'}", extra=initial_log_extra)

    if not all([run_id_str, runnable_type, runnable_id_str, db_url]):
        logger.error("FATAL: Missing required environment variables (RUN_ID, RUNNABLE_TYPE, RUNNABLE_ID, DATABASE_URL).", extra=initial_log_extra)
        sys.exit(1)

    if runnable_type not in ['agent', 'team']:
        logger.error(f"FATAL: Invalid RUNNABLE_TYPE: {runnable_type}. Must be 'agent' or 'team'.", extra=initial_log_extra)
        sys.exit(1)

    run_id: Optional[uuid.UUID] = None
    engine = None
    error_message: Optional[str] = None
    redis_handler: Optional[RedisPubSubHandler] = None # Keep track of handler instance
    log_extra = initial_log_extra # Use initial extra dict until run_id is UUID

    try:
        # Validate and convert IDs early
        try:
            run_id = uuid.UUID(run_id_str)
            runnable_id = uuid.UUID(runnable_id_str)
            input_data = json.loads(input_data_str)
            log_extra = {"run_id": run_id} # Update extra dict with UUID
            logger.info("RUN_ID, RUNNABLE_ID, INPUT_DATA successfully parsed.", extra=log_extra)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
             # Use initial_log_extra here as run_id might be invalid
             logger.error(f"FATAL: Invalid RUN_ID, RUNNABLE_ID, or INPUT_DATA format. Error: {e}", extra=initial_log_extra)
             sys.exit(1)

        # --- Initialize Redis and Add Handler ---
        try:
            await redis_service.initialize_async()
            logger.info("Redis connection initialized.", extra=log_extra)
            # Create and add Redis Handler *after* successful initialization
            redis_handler = RedisPubSubHandler(run_id=run_id)
            logger.addHandler(redis_handler)
            logger.info("RedisPubSubHandler added to logger.", extra=log_extra)
        except Exception as redis_err:
            logger.error(f"Failed to initialize Redis or add handler: {redis_err}", exc_info=True, extra=log_extra)
            # Proceed without Redis PubSub logging
            redis_handler = None # Ensure handler is None if init failed
            pass
        # --- End Redis Init ---

        # 2. Setup Database Connection
        logger.info("Setting up database connection...", extra=log_extra)
        try:
            # Use NullPool for non-persistent connections like short-lived jobs
            engine = create_async_engine(db_url, poolclass=NullPool)
            session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
            logger.info("Database engine and session maker created.", extra=log_extra)
        except Exception as e:
            logger.error(f"FATAL: Error creating database engine/session maker: {e}", extra=log_extra)
            sys.exit(1) # Exit if DB setup fails

        async with session_maker() as session:
            logger.info("Acquired DB session.", extra=log_extra)
            # Fetch Run object
            try:
                result = await session.execute(select(RunORM).where(RunORM.id == run_id))
                run = result.scalar_one_or_none()
            except Exception as e:
                logger.error(f"FATAL: Error fetching Run {run_id} from database: {e}", extra=log_extra)
                sys.exit(1) # Exit if cannot fetch run record

            if not run:
                logger.error(f"FATAL: Run {run_id} not found in database.", extra=log_extra)
                sys.exit(1) # Exit if run record doesn't exist

            if run.status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
                 logger.info(f"Run {run_id} already in terminal state: {run.status}. Exiting.", extra=log_extra)
                 final_status = run.status
                 sys.exit(0 if final_status == RunStatus.COMPLETED else 1) # Exit cleanly if already done

            # 3. Update Run Status to RUNNING
            logger.info(f"Updating Run {run_id} status to RUNNING in DB.", extra=log_extra)
            run.status = RunStatus.RUNNING
            run.started_at = datetime.utcnow()
            session.add(run)
            try:
                await session.commit()
                logger.info(f"Run {run_id} status updated to RUNNING.", extra=log_extra)
                await session.refresh(run)
            except Exception as e:
                 logger.error(f"FATAL: Error committing RUNNING status for Run {run_id}: {e}", extra=log_extra)
                 try: await session.rollback()
                 except Exception: pass
                 sys.exit(1) # Exit if cannot update status to RUNNING

            # --- Execution Block --- Within the session context ---
            final_output: Optional[Dict] = None
            try:
                # 4. Instantiate Services
                logger.info("Instantiating services...", extra=log_extra)
                agent_service = AgentService(db=session)
                team_service = None
                if runnable_type == 'team':
                    team_service = TeamService(db=session)
                logger.info("Services instantiated.", extra=log_extra)

                # 5. Create Agno Agent/Team Instance
                logger.info(f"Creating Agno {runnable_type} instance for ID: {runnable_id}...", extra=log_extra)
                if runnable_type == 'agent':
                    agno_runnable = await agent_service.create_agno_agent_instance(
                        agent_id=runnable_id,
                        tool_registry=ToolInterfaceRegistry.get_instance() # Use singleton registry
                    )
                elif runnable_type == 'team':
                     agno_runnable = await team_service.create_agno_team_instance(team_id=runnable_id)
                else:
                    # This case should be caught by earlier checks, but belts and suspenders
                    raise ServiceError(f"Invalid runnable_type '{runnable_type}' encountered during instantiation.")

                if not agno_runnable:
                     raise ServiceError(f"Failed to create Agno {runnable_type} instance.")

                logger.info(f"Agno {runnable_type} instance created successfully.", extra=log_extra)


                # 6. Execute Runnable
                logger.info(f"Executing {runnable_type} run for ID: {run_id}...", extra=log_extra)
                # Pass input_data directly to arun
                # Note: Ensure input_data keys match expected input variables of the agent/team
                final_output = await agno_runnable.arun(input=input_data)
                logger.info(f"Execution finished for run ID: {run_id}. Raw output: {str(final_output)[:100]}...", extra=log_extra) # Log snippet

                # 7. Set status to COMPLETED on success
                final_status = RunStatus.COMPLETED
                logger.info(f"Run {run_id} completed successfully.", extra=log_extra)

            # Handle specific creation/execution errors
            except (AgentCreationError, TeamCreationError, KnowledgeCreationError, StorageCreationError, ServiceError) as service_exc:
                logger.error(f"Service error during setup or execution for run {run_id}: {service_exc}", extra=log_extra)
                final_output = {"error": f"Service Error: {service_exc}"}
                error_message = str(service_exc)
                final_status = RunStatus.FAILED # Ensure failed status
            except ValueError as val_err:
                 logger.error(f"Value error (likely config issue) during setup/execution for run {run_id}: {val_err}", extra=log_extra)
                 final_output = {"error": f"Configuration Error: {val_err}"}
                 error_message = str(val_err)
                 final_status = RunStatus.FAILED # Ensure failed status
            except Exception as exec_e:
                # Catchall for other unexpected errors during execution
                logger.error(f"Unexpected error during execution for run {run_id}: {exec_e}", exc_info=True, extra=log_extra)
                final_output = {"error": f"Unexpected Execution Error: {exec_e}"}
                error_message = traceback.format_exc()
                final_status = RunStatus.FAILED # Ensure failed status

            # --- Update Run Record (Finally within session) ---
            # This runs even if execution block failed, to record the FAILED status
            if run:
                logger.info(f"Finalizing Run {run_id} with status {final_status}.", extra=log_extra)
                run.status = final_status
                run.error_message = error_message # Store error message if any
                # Store output - Ensure it's JSON serializable
                try:
                    if final_output is None: final_output = {}
                    json.dumps(final_output) # Test serialization
                    run.output_data = final_output
                except (TypeError, OverflowError) as json_err:
                    logger.warning(f"Warning: Output for run {run_id} is not JSON serializable: {json_err}. Storing as string.", extra=log_extra)
                    run.output_data = {"error": "Output not JSON serializable", "details": str(final_output)}
                except Exception as ser_err:
                     logger.warning(f"Warning: Unexpected error checking output serializability for run {run_id}: {ser_err}. Storing as string.", extra=log_extra)
                     run.output_data = {"error": "Error serializing output", "details": str(final_output)}

                if not run.started_at: run.started_at = datetime.utcnow() # Fallback if status update failed earlier
                run.ended_at = datetime.utcnow()
                session.add(run)
                try:
                    await session.commit()
                    logger.info("Final status committed to DB.", extra=log_extra)
                except Exception as final_db_err:
                    # Log error, but don't necessarily exit the whole script, let finally block handle exit code
                    logger.error(f"Error committing final status for run {run_id}: {final_db_err}", extra=log_extra)
                    final_status = RunStatus.FAILED # Mark as failed if final commit fails
            else:
                # This shouldn't happen if initial fetch worked, but log just in case
                logger.error("CRITICAL: Cannot finalize run - Run object lost within session scope?", extra=log_extra)
                final_status = RunStatus.FAILED

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
