from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict
import uuid

from mindloom.app.models.agent import Agent, AgentCreate, AgentUpdate

router = APIRouter()

# In-memory storage (replace with database interactions later)
db_agents: Dict[uuid.UUID, Agent] = {}

@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED, tags=["Agents"])
async def create_agent(agent_in: AgentCreate) -> Agent:
    """
    Create a new agent.
    """
    new_id = uuid.uuid4()
    agent = Agent(id=new_id, **agent_in.model_dump())
    db_agents[new_id] = agent
    return agent

@router.get("/", response_model=List[Agent], tags=["Agents"])
async def read_agents(
    skip: int = 0,
    limit: int = 100
) -> List[Agent]:
    """
    Retrieve a list of agents.
    """
    agents_list = list(db_agents.values())
    return agents_list[skip : skip + limit]

@router.get("/{agent_id}", response_model=Agent, tags=["Agents"])
async def read_agent(agent_id: uuid.UUID) -> Agent:
    """
    Retrieve a specific agent by ID.
    """
    agent = db_agents.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=Agent, tags=["Agents"])
async def update_agent(agent_id: uuid.UUID, agent_in: AgentUpdate) -> Agent:
    """
    Update an existing agent.
    """
    agent = db_agents.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    update_data = agent_in.model_dump(exclude_unset=True)
    updated_agent = agent.model_copy(update=update_data)
    db_agents[agent_id] = updated_agent
    return updated_agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Agents"])
async def delete_agent(agent_id: uuid.UUID) -> None:
    """
    Delete an agent.
    """
    if agent_id not in db_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    del db_agents[agent_id]
    return None # FastAPI handles the 204 No Content response
