from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from mindloom.app.models.agent import Agent, AgentCreate, AgentUpdate, AgentORM
from mindloom.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED, tags=["Agents"])
async def create_agent(agent_in: AgentCreate) -> Agent:
    """
    Create a new agent.
    """
    new_id = uuid.uuid4()
    agent = Agent(id=new_id, **agent_in.model_dump())
    # db_agents[new_id] = agent
    # Replace in-memory storage with database interaction
    async with get_db() as db:
        db_agent = AgentORM(id=new_id, **agent_in.model_dump())
        db.add(db_agent)
        await db.commit()
        await db.refresh(db_agent)
        return Agent.from_orm(db_agent)

@router.get("/", response_model=List[Agent], tags=["Agents"])
async def read_agents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[Agent]:
    """
    Retrieve a list of agents from the database.
    """
    statement = select(AgentORM).offset(skip).limit(limit)
    result = await db.execute(statement)
    agents = result.scalars().all()
    return [Agent.from_orm(agent) for agent in agents]

@router.get("/{agent_id}", response_model=Agent, tags=["Agents"])
async def read_agent(agent_id: uuid.UUID) -> Agent:
    """
    Retrieve a specific agent by ID.
    """
    async with get_db() as db:
        statement = select(AgentORM).where(AgentORM.id == agent_id)
        result = await db.execute(statement)
        agent = result.scalars().first()
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        return Agent.from_orm(agent)

@router.put("/{agent_id}", response_model=Agent, tags=["Agents"])
async def update_agent(agent_id: uuid.UUID, agent_in: AgentUpdate) -> Agent:
    """
    Update an existing agent.
    """
    async with get_db() as db:
        statement = select(AgentORM).where(AgentORM.id == agent_id)
        result = await db.execute(statement)
        agent = result.scalars().first()
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

        update_data = agent_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(agent, key, value)
        await db.commit()
        await db.refresh(agent)
        return Agent.from_orm(agent)

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Agents"])
async def delete_agent(agent_id: uuid.UUID) -> None:
    """
    Delete an agent.
    """
    async with get_db() as db:
        statement = select(AgentORM).where(AgentORM.id == agent_id)
        result = await db.execute(statement)
        agent = result.scalars().first()
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        await db.delete(agent)
        await db.commit()
    return None # FastAPI handles the 204 No Content response
