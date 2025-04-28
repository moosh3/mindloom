from fastapi import APIRouter

from mindloom.app.api.v1.endpoints import agents
from mindloom.app.api.v1.endpoints import teams
from mindloom.app.api.v1.endpoints import runs

api_router = APIRouter()

# Include endpoint routers here
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(runs.router, prefix="/runs", tags=["Runs"])

# Future routers would be included here
# api_router.include_router(..., prefix="/...", tags=["..."])
