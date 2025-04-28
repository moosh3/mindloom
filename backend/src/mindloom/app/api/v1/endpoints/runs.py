from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Optional
import uuid
from datetime import datetime

from mindloom.app.models.run import Run, RunCreate, RunStatus
# Import agent/team endpoints to potentially check runnable_id later
# from .agents import db_agents
# from .teams import db_teams

router = APIRouter()

# In-memory storage (replace with database interactions later)
db_runs: Dict[uuid.UUID, Run] = {}

@router.post("/", response_model=Run, status_code=status.HTTP_202_ACCEPTED, tags=["Runs"])
async def create_run(run_in: RunCreate) -> Run:
    """
    Start a new run for an agent or team.

    (Note: This currently just creates the record, actual execution logic TBD)
    """
    # Basic validation (can be enhanced later)
    if run_in.runnable_type not in ['agent', 'team']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid runnable_type. Must be 'agent' or 'team'.")

    # TODO: Later, add check to ensure run_in.runnable_id exists in db_agents or db_teams

    new_id = uuid.uuid4()
    # Create the Run record with PENDING status
    run = Run(
        id=new_id,
        status=RunStatus.PENDING,
        created_at=datetime.utcnow(), # Set creation time now
        **run_in.model_dump()
    )
    db_runs[new_id] = run

    # TODO: Trigger actual background execution task here

    return run # Return the created run record

@router.get("/", response_model=List[Run], tags=["Runs"])
async def read_runs(
    skip: int = 0,
    limit: int = 100,
    runnable_id: Optional[uuid.UUID] = None, # Optional filter by agent/team
    status: Optional[RunStatus] = None       # Optional filter by status
) -> List[Run]:
    """
    Retrieve a list of runs, with optional filtering.
    """
    runs_list = list(db_runs.values())

    # Apply filters if provided
    if runnable_id:
        runs_list = [run for run in runs_list if run.runnable_id == runnable_id]
    if status:
        runs_list = [run for run in runs_list if run.status == status]

    # Apply sorting (e.g., newest first)
    runs_list.sort(key=lambda r: r.created_at, reverse=True)

    return runs_list[skip : skip + limit]

@router.get("/{run_id}", response_model=Run, tags=["Runs"])
async def read_run(run_id: uuid.UUID) -> Run:
    """
    Retrieve a specific run by ID.
    """
    run = db_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run

# Potential future endpoint: Cancel a run
# @router.post("/{run_id}/cancel", response_model=Run, tags=["Runs"])
# async def cancel_run(run_id: uuid.UUID) -> Run:
#     ...
