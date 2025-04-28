from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
import uuid

from mindloom.app.models.team import Team, TeamCreate, TeamUpdate
# We might need Agent model if we validate agent_ids later
# from mindloom.app.models.agent import Agent 

router = APIRouter()

# In-memory storage (replace with database interactions later)
db_teams: Dict[uuid.UUID, Team] = {}

@router.post("/", response_model=Team, status_code=status.HTTP_201_CREATED, tags=["Teams"])
async def create_team(team_in: TeamCreate) -> Team:
    """
    Create a new team.
    """
    # TODO: Add validation later to ensure agent_ids exist in db_agents
    new_id = uuid.uuid4()
    team = Team(id=new_id, **team_in.model_dump())
    db_teams[new_id] = team
    return team

@router.get("/", response_model=List[Team], tags=["Teams"])
async def read_teams(
    skip: int = 0,
    limit: int = 100
) -> List[Team]:
    """
    Retrieve a list of teams.
    """
    teams_list = list(db_teams.values())
    return teams_list[skip : skip + limit]

@router.get("/{team_id}", response_model=Team, tags=["Teams"])
async def read_team(team_id: uuid.UUID) -> Team:
    """
    Retrieve a specific team by ID.
    """
    team = db_teams.get(team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team

@router.put("/{team_id}", response_model=Team, tags=["Teams"])
async def update_team(team_id: uuid.UUID, team_in: TeamUpdate) -> Team:
    """
    Update an existing team.
    """
    team = db_teams.get(team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # TODO: Add validation for agent_ids if provided in team_in
    update_data = team_in.model_dump(exclude_unset=True)
    updated_team = team.model_copy(update=update_data)
    db_teams[team_id] = updated_team
    return updated_team

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Teams"])
async def delete_team(team_id: uuid.UUID) -> None:
    """
    Delete a team.
    """
    if team_id not in db_teams:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    del db_teams[team_id]
    return None # FastAPI handles the 204 No Content response
