from fastapi import APIRouter

from mindloom.app.api.v1.endpoints import auth, agents, teams
from mindloom.app.api.v1.endpoints import content_buckets

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(content_buckets.router, prefix="/content_buckets", tags=["Content Buckets"])
# Note: The prefix here is redundant with the one in content_buckets.py, but FastAPI handles it.
# Alternatively, remove the prefix from content_buckets.py router definition.
# Add other routers here as needed
