from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mindloom.app.models.agent import Agent, AgentCreate, AgentUpdate, AgentORM
from mindloom.app.models.content_bucket import ContentBucketORM
from mindloom.app.models.user import User
from mindloom.dependencies import get_db, get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

# Define potential error responses
not_found_response = {status.HTTP_404_NOT_FOUND: {"description": "Agent not found"}}
bad_bucket_response = {status.HTTP_400_BAD_REQUEST: {"description": "Invalid Content Bucket ID(s) provided"}}

@router.post(
    "/",
    response_model=Agent,
    status_code=status.HTTP_201_CREATED,
    tags=["Agents"],
    responses={**bad_bucket_response} # Document potential 400 error
)
async def create_agent(agent_in: AgentCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Agent:
    """
    Creates a new agent associated with the current user.

    - **agent_in**: Agent details including name, configuration, and optional content bucket IDs.
    - **Returns**: The newly created agent object.
    """
    new_id = uuid.uuid4()
    agent_data = agent_in.model_dump(exclude={'content_bucket_ids'})
    content_bucket_ids = agent_in.content_bucket_ids

    # Associate agent with the current user
    async with db:
        db_agent = AgentORM(id=new_id, **agent_data, owner_id=current_user.id)

        # Handle Content Bucket relationships
        if content_bucket_ids:
            bucket_statement = select(ContentBucketORM).where(ContentBucketORM.id.in_(content_bucket_ids))
            result = await db.execute(bucket_statement)
            fetched_buckets = result.scalars().all()
            if len(fetched_buckets) != len(content_bucket_ids):
                found_ids = {b.id for b in fetched_buckets}
                missing_ids = [str(bid) for bid in content_bucket_ids if bid not in found_ids]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"One or more content bucket IDs not found: {', '.join(missing_ids)}"
                )
            db_agent.content_buckets = fetched_buckets
        else:
            db_agent.content_buckets = [] # Ensure it's an empty list if IDs are None/empty

        db.add(db_agent)
        await db.commit()
        await db.refresh(db_agent, attribute_names=['content_buckets']) # Refresh the relationship too
        # Return the ORM model directly, FastAPI handles serialization via response_model
        return db_agent # Return ORM instance

@router.get("/", response_model=List[Agent], tags=["Agents"])
async def read_agents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[Agent]:
    """
    Retrieves a list of agents, supporting pagination.

    - **skip**: Number of agents to skip.
    - **limit**: Maximum number of agents to return.
    - **Returns**: A list of agent objects.
    """
    statement = select(AgentORM).offset(skip).limit(limit)
    result = await db.execute(statement)
    agents = result.scalars().all()
    # Return list of ORM models, FastAPI handles serialization
    return agents # Return list of ORM instances

@router.get(
    "/{agent_id}",
    response_model=Agent,
    tags=["Agents"],
    responses={**not_found_response} # Document potential 404 error
)
async def read_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Agent:
    """
    Retrieves a specific agent by its unique ID.

    - **agent_id**: The UUID of the agent to retrieve.
    - **Returns**: The requested agent object.
    - **Raises**: `HTTPException` (404) if the agent is not found.
    """
    statement = select(AgentORM).where(AgentORM.id == agent_id).options(selectinload(AgentORM.content_buckets)) # Eager load buckets
    result = await db.execute(statement)
    agent = result.scalars().first()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    # Return the ORM model
    return agent # Return ORM instance

@router.put(
    "/{agent_id}",
    response_model=Agent,
    tags=["Agents"],
    responses={**not_found_response, **bad_bucket_response} # Document potential 404/400 errors
)
async def update_agent(
    agent_id: uuid.UUID,
    agent_in: AgentUpdate,
    db: AsyncSession = Depends(get_db)
) -> Agent:
    """
    Updates an existing agent.

    Allows partial updates. Only fields provided in the request body will be updated.
    To remove all content buckets, provide an empty `content_bucket_ids` list.

    - **agent_id**: The UUID of the agent to update.
    - **agent_in**: An object containing the fields to update.
    - **Returns**: The updated agent object.
    - **Raises**: `HTTPException` (404) if the agent is not found.
    - **Raises**: `HTTPException` (400) if invalid `content_bucket_ids` are provided.
    """
    statement = select(AgentORM).where(AgentORM.id == agent_id).options(selectinload(AgentORM.content_buckets))
    result = await db.execute(statement)
    agent = result.scalars().first()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    update_data = agent_in.model_dump(exclude_unset=True)
    content_bucket_ids = update_data.pop('content_bucket_ids', None) # Handle specifically

    # Update Content Bucket relationships if provided
    if content_bucket_ids is not None:
        if not content_bucket_ids: # Empty list means remove all buckets
            agent.content_buckets = []
        else:
            bucket_statement = select(ContentBucketORM).where(ContentBucketORM.id.in_(content_bucket_ids))
            result = await db.execute(bucket_statement)
            fetched_buckets = result.scalars().all()
            if len(fetched_buckets) != len(content_bucket_ids):
                found_ids = {b.id for b in fetched_buckets}
                missing_ids = [str(bid) for bid in content_bucket_ids if bid not in found_ids]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"One or more content bucket IDs not found: {', '.join(missing_ids)}"
                )
            agent.content_buckets = fetched_buckets

    # Update other fields
    for key, value in update_data.items():
        setattr(agent, key, value)
    await db.commit()
    await db.refresh(agent, attribute_names=['content_buckets']) # Refresh the relationship
    # Return the ORM model
    return agent # Return ORM instance

@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Agents"],
    responses={**not_found_response} # Document potential 404 error
)
async def delete_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Deletes a specific agent by its unique ID.

    - **agent_id**: The UUID of the agent to delete.
    - **Returns**: `None` with a 204 status code on success.
    - **Raises**: `HTTPException` (404) if the agent is not found.
    """
    statement = select(AgentORM).where(AgentORM.id == agent_id)
    result = await db.execute(statement)
    agent = result.scalars().first()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    await db.delete(agent)
    await db.commit()
    return None # FastAPI handles the 204 No Content response

# --- Agent-Content Bucket Association Endpoints --- #

@router.post(
    "/{agent_id}/content_buckets/{bucket_id}",
    response_model=Agent,
    tags=["Agents"],
    summary="Associate Content Bucket with Agent",
    responses={**not_found_response, status.HTTP_404_NOT_FOUND: {"description": "Content Bucket not found"}}
)
async def associate_agent_content_bucket(
    agent_id: uuid.UUID,
    bucket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Agent:
    """
    Associates a specific Content Bucket with an Agent.

    - **agent_id**: The UUID of the agent.
    - **bucket_id**: The UUID of the content bucket to associate.
    - **Returns**: The updated agent object with the new association.
    - **Raises**: `HTTPException` (404) if the agent or content bucket is not found.
    """
    # Fetch Agent with buckets preloaded
    agent_stmt = select(AgentORM).where(AgentORM.id == agent_id).options(selectinload(AgentORM.content_buckets))
    agent_result = await db.execute(agent_stmt)
    agent = agent_result.scalars().first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    # Fetch Content Bucket
    bucket_stmt = select(ContentBucketORM).where(ContentBucketORM.id == bucket_id)
    bucket_result = await db.execute(bucket_stmt)
    bucket = bucket_result.scalars().first()
    if not bucket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content Bucket not found")

    # Add association if not already present
    if bucket not in agent.content_buckets:
        agent.content_buckets.append(bucket)
        await db.commit()
        await db.refresh(agent, attribute_names=['content_buckets'])

    return agent # Return updated ORM instance

@router.delete(
    "/{agent_id}/content_buckets/{bucket_id}",
    response_model=Agent,
    tags=["Agents"],
    summary="Dissociate Content Bucket from Agent",
    responses={**not_found_response, status.HTTP_404_NOT_FOUND: {"description": "Content Bucket not found"}}
)
async def dissociate_agent_content_bucket(
    agent_id: uuid.UUID,
    bucket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Agent:
    """
    Dissociates a specific Content Bucket from an Agent.

    - **agent_id**: The UUID of the agent.
    - **bucket_id**: The UUID of the content bucket to dissociate.
    - **Returns**: The updated agent object without the association.
    - **Raises**: `HTTPException` (404) if the agent or content bucket is not found.
    """
    # Fetch Agent with buckets preloaded
    agent_stmt = select(AgentORM).where(AgentORM.id == agent_id).options(selectinload(AgentORM.content_buckets))
    agent_result = await db.execute(agent_stmt)
    agent = agent_result.scalars().first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    # Find the bucket in the agent's list
    bucket_to_remove = next((b for b in agent.content_buckets if b.id == bucket_id), None)

    if bucket_to_remove:
        agent.content_buckets.remove(bucket_to_remove)
        await db.commit()
        await db.refresh(agent, attribute_names=['content_buckets'])
    # If bucket wasn't associated, no error, just return current state
    # If bucket ID itself doesn't exist, we could 404, but maybe unnecessary
    # Let's keep it simple: if associated, remove; otherwise, do nothing.

    return agent # Return updated (or unchanged) ORM instance
