import os
import sys
import uuid
import json
from datetime import datetime
import asyncio
from typing import Dict, Any, Optional, Union

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

# TODO: Set up proper logging
print("Initializing Mindloom Run Executor...")

async def main():
    print("Starting main execution block...")

    # 1. Read Environment Variables
    run_id_str = os.getenv("RUN_ID")
    runnable_type = os.getenv("RUNNABLE_TYPE")
    runnable_id_str = os.getenv("RUNNABLE_ID")
    input_data_str = os.getenv("INPUT_DATA", "{}")
    db_url = os.getenv("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL") # Used by services

    print(f"RUN_ID: {run_id_str}")
    print(f"RUNNABLE_TYPE: {runnable_type}")
    print(f"RUNNABLE_ID: {runnable_id_str}")
    print(f"DATABASE_URL: {'*' * 5 if db_url else 'Not Set'}")
    print(f"REDIS_URL: {'*' * 5 if redis_url else 'Not Set'}")

    if not all([run_id_str, runnable_type, runnable_id_str, db_url]):
        print("Error: Missing required environment variables (RUN_ID, RUNNABLE_TYPE, RUNNABLE_ID, DATABASE_URL).")
        sys.exit(1)

    if runnable_type not in ['agent', 'team']:
        print(f"Error: Invalid RUNNABLE_TYPE: {runnable_type}. Must be 'agent' or 'team'.")
        sys.exit(1)

    run_id: Optional[uuid.UUID] = None
    engine = None
    session_maker = None
    run: Optional[RunORM] = None
    final_status: RunStatus = RunStatus.FAILED

    try:
        run_id = uuid.UUID(run_id_str)
        runnable_id = uuid.UUID(runnable_id_str)
        input_data = json.loads(input_data_str)

        # 2. Setup Database Connection
        print(f"Connecting to database: {db_url[:15]}...")
        try:
            engine = create_async_engine(db_url, poolclass=NullPool)
            session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
            print("Database engine and session maker created.")
        except Exception as e:
            print(f"Error creating database engine/session maker: {e}")
            sys.exit(1)

        async with session_maker() as session:
            print("Acquired DB session.")
            # Fetch Run object
            try:
                result = await session.execute(select(RunORM).where(RunORM.id == run_id))
                run = result.scalars().first()
            except Exception as e:
                 print(f"Error fetching Run {run_id} from database: {e}")
                 sys.exit(1)

            if not run:
                print(f"Error: Run {run_id} not found in database.")
                sys.exit(1)

            if run.status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
                 print(f"Run {run_id} already in terminal state: {run.status}. Exiting.")
                 final_status = run.status
                 sys.exit(0 if final_status == RunStatus.COMPLETED else 1)

            # 3. Update Run Status to RUNNING
            print(f"Updating Run {run_id} status to RUNNING in DB.")
            run.status = RunStatus.RUNNING
            run.started_at = datetime.utcnow()
            session.add(run)
            try:
                await session.commit()
                print(f"Run {run_id} status updated to RUNNING.")
                await session.refresh(run)
            except Exception as e:
                 print(f"Error committing RUNNING status for Run {run_id}: {e}")
                 try: await session.rollback()
                 except Exception: pass
                 sys.exit(1)

            # --- Execution Block --- Within the session context ---
            final_output: Optional[Dict] = None
            agno_runnable: Optional[Union[AgnoAgent, AgnoTeam]] = None
            try:
                # 4. Instantiate Services
                print("Instantiating services...")
                agent_service = AgentService(db=session)
                team_service = None
                if runnable_type == 'team':
                    team_service = TeamService(db=session, agent_service=agent_service)
                print("Services instantiated.")

                # 5. Create Agno Agent/Team Instance
                print(f"Creating Agno {runnable_type} instance for ID: {runnable_id}...")
                if runnable_type == 'agent':
                    agno_runnable = await agent_service.create_agno_agent_instance(
                        agent_id=runnable_id,
                        session_id=run_id # Pass run_id as session_id for agent
                    )
                elif runnable_type == 'team' and team_service:
                    agno_runnable = await team_service.create_agno_team_instance(
                        team_id=runnable_id
                    )
                else:
                    # Should not happen due to initial validation, but good practice
                    raise ServiceError(f"Invalid runnable_type '{runnable_type}' encountered during instantiation.")

                if not agno_runnable:
                     raise ServiceError(f"Failed to create Agno {runnable_type} instance.")

                print(f"Agno {runnable_type} instance created successfully.")

                # 6. Execute Runnable
                print(f"Executing {runnable_type} run for ID: {run_id}...")
                # Pass input_data directly to arun
                # Note: Ensure input_data keys match expected input variables of the agent/team
                final_output = await agno_runnable.arun(input=input_data)
                print(f"Execution finished for run ID: {run_id}. Raw output: {str(final_output)[:100]}...") # Log snippet

                # 7. Set status to COMPLETED on success
                final_status = RunStatus.COMPLETED
                print(f"Run {run_id} completed successfully.")

            # Handle specific creation/execution errors
            except (AgentCreationError, TeamCreationError, KnowledgeCreationError, StorageCreationError, ServiceError) as service_exc:
                print(f"Service error during setup or execution for run {run_id}: {service_exc}")
                final_output = {"error": f"Service Error: {service_exc}"}
                # final_status remains FAILED
            except ValueError as val_err:
                 print(f"Value error (likely config issue) during setup/execution for run {run_id}: {val_err}")
                 final_output = {"error": f"Configuration Error: {val_err}"}
                 # final_status remains FAILED
            except Exception as exec_e:
                # Catchall for other unexpected errors during execution
                print(f"Unexpected error during execution for run {run_id}: {exec_e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                final_output = {"error": f"Unexpected Execution Error: {exec_e}"}
                # final_status remains FAILED

            # --- Final DB Update --- Still within the session context ---
            if run:
                print(f"Finalizing Run {run_id} with status {final_status}.")
                run.status = final_status
                # Store output - Ensure it's JSON serializable
                try:
                    # Attempt to serialize output directly. If it fails, store a string representation.
                    json.dumps(final_output) # Test serialization
                    run.output_data = final_output
                except (TypeError, OverflowError) as json_err:
                    print(f"Warning: Output for run {run_id} is not JSON serializable: {json_err}. Storing as string.")
                    run.output_data = {"error": "Output not JSON serializable", "details": str(final_output)}
                except Exception as ser_err:
                     print(f"Warning: Unexpected error checking output serializability for run {run_id}: {ser_err}. Storing as string.")
                     run.output_data = {"error": "Error serializing output", "details": str(final_output)}

                if not run.started_at: run.started_at = datetime.utcnow()
                run.ended_at = datetime.utcnow()
                session.add(run)
                try:
                    await session.commit()
                    print("Final status committed to DB.")
                except Exception as final_db_err:
                    print(f"Error committing final status for run {run_id}: {final_db_err}")
                    final_status = RunStatus.FAILED
            else:
                print("Error: Cannot finalize run - Run object lost within session scope?")
                final_status = RunStatus.FAILED

    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error parsing environment variables: {e}")
        sys.exit(1)
    except Exception as setup_e:
        print(f"Unexpected error during setup: {setup_e}")
        sys.exit(1)
    finally:
        if engine:
            await engine.dispose()
            print("Database engine disposed.")

    print("Mindloom Run Executor finished.")
    sys.exit(0 if final_status == RunStatus.COMPLETED else 1)

if __name__ == "__main__":
    asyncio.run(main())
