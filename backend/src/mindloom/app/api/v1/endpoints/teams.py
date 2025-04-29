from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, AsyncGenerator
import uuid
import logging
import json

# Updated imports for DB operations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Updated model imports
from mindloom.app.models.team import Team, TeamCreate, TeamORM, TeamUpdate, TeamRunInput, TeamRunOutput
from mindloom.app.models.agent import AgentORM
from mindloom.dependencies import get_db, get_current_user, get_team_service
from mindloom.services.teams import TeamService
from mindloom.services.exceptions import AgentCreationError, TeamCreationError, ServiceError
from fastapi.responses import StreamingResponse

# Add the dependency here
router = APIRouter(dependencies=[Depends(get_current_user)])

logger = logging.getLogger(__name__)

@router.post("/", response_model=Team, status_code=status.HTTP_201_CREATED, tags=["Teams"])
async def create_team(
    team_in: TeamCreate,
    db: AsyncSession = Depends(get_db)
) -> Team:
    """Create a new team."""
    # Separate agent_ids from other data
    team_data = team_in.model_dump(exclude={'agent_ids'})
    db_team = TeamORM(**team_data)

    # Fetch AgentORM objects if agent_ids are provided
    if team_in.agent_ids:
        agent_statement = select(AgentORM).where(AgentORM.id.in_(team_in.agent_ids))
        result = await db.execute(agent_statement)
        agents = result.scalars().all()
        if len(agents) != len(team_in.agent_ids):
            found_ids = {agent.id for agent in agents}
            missing_ids = [str(aid) for aid in team_in.agent_ids if aid not in found_ids]
            raise HTTPException(
                status_code=400, 
                detail=f"One or more agent IDs not found: {', '.join(missing_ids)}"
            )
        db_team.agents = agents

    db.add(db_team)
    await db.commit()
    await db.refresh(db_team, attribute_names=['agents'])
    return Team.from_orm(db_team)

@router.get("/", response_model=List[Team], tags=["Teams"])
async def read_teams(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[Team]:
    """Retrieve a list of teams."""
    statement = (
        select(TeamORM)
        .options(selectinload(TeamORM.agents))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(statement)
    teams = result.scalars().all()
    return [Team.from_orm(team) for team in teams]

@router.get("/{team_id}", response_model=Team, tags=["Teams"])
async def read_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Team:
    """Retrieve a specific team by ID."""
    statement = (
        select(TeamORM)
        .options(selectinload(TeamORM.agents))
        .where(TeamORM.id == team_id)
    )
    result = await db.execute(statement)
    team = result.scalars().first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return Team.from_orm(team)

@router.put("/{team_id}", response_model=Team, tags=["Teams"])
async def update_team(
    team_id: uuid.UUID,
    team_in: TeamUpdate,
    db: AsyncSession = Depends(get_db)
) -> Team:
    """Update an existing team."""
    statement = select(TeamORM).options(selectinload(TeamORM.agents)).where(TeamORM.id == team_id)
    result = await db.execute(statement)
    team = result.scalars().first()

    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    update_data = team_in.model_dump(exclude_unset=True)

    if 'agent_ids' in update_data:
        agent_ids = update_data.pop('agent_ids')
        if agent_ids is not None:
            if not agent_ids:
                team.agents = []
            else:
                agent_statement = select(AgentORM).where(AgentORM.id.in_(agent_ids))
                result = await db.execute(agent_statement)
                agents = result.scalars().all()
                if len(agents) != len(agent_ids):
                    found_ids = {agent.id for agent in agents}
                    missing_ids = [str(aid) for aid in agent_ids if aid not in found_ids]
                    raise HTTPException(
                        status_code=400, 
                        detail=f"One or more agent IDs not found for update: {', '.join(missing_ids)}"
                    )
                team.agents = agents

    for key, value in update_data.items():
        setattr(team, key, value)

    await db.commit()
    await db.refresh(team, attribute_names=['agents'])
    return Team.from_orm(team)

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Teams"])
async def delete_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a team."""
    statement = select(TeamORM).where(TeamORM.id == team_id)
    result = await db.execute(statement)
    team = result.scalars().first()

    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    await db.delete(team)
    await db.commit()
    return None

@router.post("/{team_id}/run", status_code=status.HTTP_200_OK, tags=["Teams"],
    responses={
        200: {
            "content": {"application/x-ndjson": {}},
            "description": "Successful streaming response."
        },
        404: {"description": "Team not found"},
        500: {"description": "Internal server error during instantiation or streaming"}
    }
)
async def run_team(
    team_id: uuid.UUID,
    run_input: TeamRunInput,
    team_service: TeamService = Depends(get_team_service)
) -> StreamingResponse:
    """Creates an Agno Team instance and runs it with the given input."""
    logger.info(f"Received run request for team ID: {team_id}")
    try:
        agno_team = await team_service.create_agno_team_instance(team_id)
    except ValueError as ve: 
        logger.warning(f"Run request failed: Team ID {team_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except AgentCreationError as ace:
        logger.error(f"Run request failed: Error creating agents for team {team_id}: {ace}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create team agents: {ace}")
    except TeamCreationError as tce:
        logger.error(f"Run request failed: Error creating team instance {team_id}: {tce}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create team instance: {tce}")
    except ServiceError as se:
        logger.error(f"Run request failed: Service error for team {team_id}: {se}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A service error occurred: {se}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during team {team_id} instantiation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during team setup."
        )

    if not agno_team: 
        logger.error(f"Team instance for {team_id} is None after creation block, this indicates an issue.")
        raise HTTPException(status_code=500, detail="Internal error: Team instance is unexpectedly null.")

    async def stream_generator() -> AsyncGenerator[str, None]:
        """Async generator to stream chunks from agno_team.aprint_response."""
        logger.info(f"Starting streaming execution for team {team_id}...")
        try:
            async for chunk in agno_team.aprint_response(input=run_input.input):
                # Assuming chunk is JSON-serializable (dict, str, etc.)
                # Format as newline-delimited JSON (ndjson)
                try:
                    yield json.dumps(chunk) + "\n"
                except TypeError:
                    # Handle non-serializable chunks if necessary
                    logger.warning(f"Team {team_id} yielded non-JSON serializable chunk: {type(chunk)}")
                    # Optionally yield a placeholder or skip
                    yield json.dumps({"type": "log", "content": f"[Non-serializable chunk: {type(chunk)}]"}) + "\n"

            logger.info(f"Team {team_id} streaming execution finished.")
        except Exception as e:
            # Catch errors specifically from the Agno execution phase
            logger.exception(f"Error during team {team_id} streaming execution: {e}")
            # How to signal error mid-stream? Best practice is often to stop yielding
            # or yield a specific error object. For now, just log.
            # Yield a final error message to the client
            error_payload = json.dumps({"error": f"An error occurred during team execution: {e}"}) + "\n"
            yield error_payload
            # Re-raising might be better for centralized handling if FastAPI supports it well for generators
            # raise HTTPException(status_code=500, detail=f"Stream error: {e}") # This likely won't work as headers are sent

    # Return the StreamingResponse with the generator
    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
