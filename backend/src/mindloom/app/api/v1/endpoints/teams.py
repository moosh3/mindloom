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
from mindloom.app.models.content_bucket import ContentBucketORM
from mindloom.dependencies import get_db, get_current_user, get_team_service
from mindloom.services.teams import TeamService
from mindloom.services.exceptions import AgentCreationError, TeamCreationError, ServiceError
from fastapi.responses import StreamingResponse

# Add the dependency here
router = APIRouter(dependencies=[Depends(get_current_user)])

# Define potential error responses
not_found_response = {status.HTTP_404_NOT_FOUND: {"description": "Team not found"}}
bad_agent_response = {status.HTTP_400_BAD_REQUEST: {"description": "Invalid Agent ID(s) provided"}}
bad_bucket_response = {status.HTTP_400_BAD_REQUEST: {"description": "Invalid Content Bucket ID(s) provided"}}

logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=Team,
    status_code=status.HTTP_201_CREATED,
    tags=["Teams"],
    responses={**bad_agent_response, **bad_bucket_response} # Document potential 400 errors
)
async def create_team(
    team_in: TeamCreate,
    db: AsyncSession = Depends(get_db)
) -> Team:
    """Create a new team."""
    # Separate agent_ids and content_bucket_ids from other data
    team_data = team_in.model_dump(exclude={'agent_ids', 'content_bucket_ids'})
    db_team = TeamORM(**team_data)

    # Fetch AgentORM objects if agent_ids are provided
    if team_in.agent_ids:
        agent_statement = select(AgentORM).where(AgentORM.id.in_(team_in.agent_ids))
        result = await db.execute(agent_statement)
        agents = result.scalars().all()
        if len(agents) != len(set(team_in.agent_ids)): # Use set for uniqueness check
            found_ids = {agent.id for agent in agents}
            missing_ids = [str(aid) for aid in set(team_in.agent_ids) if aid not in found_ids]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Corrected status code
                detail=f"One or more agent IDs not found: {', '.join(missing_ids)}"
            )
        db_team.agents = agents

    # Fetch ContentBucketORM objects if content_bucket_ids are provided
    if team_in.content_bucket_ids:
        bucket_statement = select(ContentBucketORM).where(ContentBucketORM.id.in_(team_in.content_bucket_ids))
        bucket_result = await db.execute(bucket_statement)
        buckets = bucket_result.scalars().all()
        if len(buckets) != len(set(team_in.content_bucket_ids)): # Use set for uniqueness check
            found_ids = {bucket.id for bucket in buckets}
            missing_ids = [str(bid) for bid in set(team_in.content_bucket_ids) if bid not in found_ids]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"One or more content bucket IDs not found: {', '.join(missing_ids)}"
            )
        db_team.content_buckets = buckets

    db.add(db_team)
    await db.commit()
    # Refresh both relationships
    await db.refresh(db_team, attribute_names=['agents', 'content_buckets'])
    # Return ORM instance, FastAPI uses pydantic model's from_orm
    return db_team

@router.get("/", response_model=List[Team], tags=["Teams"])
async def read_teams(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[Team]:
    """Retrieve a list of teams."""
    statement = (
        select(TeamORM)
        # Eager load both relationships
        .options(selectinload(TeamORM.agents), selectinload(TeamORM.content_buckets))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(statement)
    teams = result.scalars().unique().all() # Use unique() to handle potential duplicates from eager loading
    # Return list of ORM instances
    return teams

@router.get(
    "/{team_id}",
    response_model=Team,
    tags=["Teams"],
    responses={**not_found_response}
)
async def read_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Team:
    """Retrieve a specific team by ID."""
    statement = (
        select(TeamORM)
        # Eager load both relationships
        .options(selectinload(TeamORM.agents), selectinload(TeamORM.content_buckets))
        .where(TeamORM.id == team_id)
    )
    result = await db.execute(statement)
    team = result.scalars().first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    # Return ORM instance
    return team

@router.put(
    "/{team_id}",
    response_model=Team,
    tags=["Teams"],
    responses={**not_found_response, **bad_agent_response, **bad_bucket_response}
)
async def update_team(
    team_id: uuid.UUID,
    team_in: TeamUpdate,
    db: AsyncSession = Depends(get_db)
) -> Team:
    """Update an existing team."""
    statement = select(TeamORM).options(
        selectinload(TeamORM.agents),
        selectinload(TeamORM.content_buckets)
    ).where(TeamORM.id == team_id)
    result = await db.execute(statement)
    team = result.scalars().first()

    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    update_data = team_in.model_dump(exclude_unset=True)

    # Handle agent associations
    if 'agent_ids' in update_data:
        agent_ids = update_data.pop('agent_ids')
        if agent_ids is not None:
            if not agent_ids: # Empty list means remove all agents
                team.agents = []
            else:
                agent_statement = select(AgentORM).where(AgentORM.id.in_(agent_ids))
                agent_result = await db.execute(agent_statement)
                agents = agent_result.scalars().all()
                if len(agents) != len(set(agent_ids)): # Use set for uniqueness
                    found_ids = {agent.id for agent in agents}
                    missing_ids = [str(aid) for aid in set(agent_ids) if aid not in found_ids]
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"One or more agent IDs not found: {', '.join(missing_ids)}"
                    )
                team.agents = agents

    # Handle content bucket associations
    if 'content_bucket_ids' in update_data:
        bucket_ids = update_data.pop('content_bucket_ids')
        if bucket_ids is not None:
            if not bucket_ids: # Empty list means remove all buckets
                team.content_buckets = []
            else:
                bucket_statement = select(ContentBucketORM).where(ContentBucketORM.id.in_(bucket_ids))
                bucket_result = await db.execute(bucket_statement)
                buckets = bucket_result.scalars().all()
                if len(buckets) != len(set(bucket_ids)): # Use set for uniqueness
                    found_ids = {bucket.id for bucket in buckets}
                    missing_ids = [str(bid) for bid in set(bucket_ids) if bid not in found_ids]
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"One or more content bucket IDs not found: {', '.join(missing_ids)}"
                    )
                team.content_buckets = buckets

    # Update other team attributes
    for key, value in update_data.items():
        setattr(team, key, value)

    await db.commit()
    # Refresh relationships
    await db.refresh(team, attribute_names=['agents', 'content_buckets'])
    # Return ORM instance
    return team

@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Teams"],
    responses={**not_found_response}
)
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


# --- Team-Content Bucket Association Endpoints --- #

@router.post(
    "/{team_id}/content_buckets/{bucket_id}",
    response_model=Team,
    tags=["Teams"],
    summary="Associate Content Bucket with Team",
    responses={**not_found_response, status.HTTP_404_NOT_FOUND: {"description": "Content Bucket not found"}}
)
async def associate_team_content_bucket(
    team_id: uuid.UUID,
    bucket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Team:
    """
    Associates a specific Content Bucket with a Team.

    - **team_id**: The UUID of the team.
    - **bucket_id**: The UUID of the content bucket to associate.
    - **Returns**: The updated team object with the new association.
    - **Raises**: `HTTPException` (404) if the team or content bucket is not found.
    """
    # Fetch Team with buckets preloaded
    team_stmt = select(TeamORM).where(TeamORM.id == team_id).options(selectinload(TeamORM.content_buckets))
    team_result = await db.execute(team_stmt)
    team = team_result.scalars().first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Fetch Content Bucket
    bucket_stmt = select(ContentBucketORM).where(ContentBucketORM.id == bucket_id)
    bucket_result = await db.execute(bucket_stmt)
    bucket = bucket_result.scalars().first()
    if not bucket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content Bucket not found")

    # Add association if not already present
    if bucket not in team.content_buckets:
        team.content_buckets.append(bucket)
        await db.commit()
        await db.refresh(team, attribute_names=['content_buckets'])

    return team # Return updated ORM instance

@router.delete(
    "/{team_id}/content_buckets/{bucket_id}",
    response_model=Team,
    tags=["Teams"],
    summary="Dissociate Content Bucket from Team",
    responses={**not_found_response, status.HTTP_404_NOT_FOUND: {"description": "Content Bucket not found"}}
)
async def dissociate_team_content_bucket(
    team_id: uuid.UUID,
    bucket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Team:
    """
    Dissociates a specific Content Bucket from a Team.

    - **team_id**: The UUID of the team.
    - **bucket_id**: The UUID of the content bucket to dissociate.
    - **Returns**: The updated team object without the association.
    - **Raises**: `HTTPException` (404) if the team or content bucket is not found.
    """
    # Fetch Team with buckets preloaded
    team_stmt = select(TeamORM).where(TeamORM.id == team_id).options(selectinload(TeamORM.content_buckets))
    team_result = await db.execute(team_stmt)
    team = team_result.scalars().first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Find the bucket in the team's list
    bucket_to_remove = next((b for b in team.content_buckets if b.id == bucket_id), None)

    if bucket_to_remove:
        team.content_buckets.remove(bucket_to_remove)
        await db.commit()
        await db.refresh(team, attribute_names=['content_buckets'])
    # If bucket wasn't associated, no error, just return current state

    return team # Return updated (or unchanged) ORM instance
