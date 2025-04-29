from fastapi import FastAPI
from mindloom.app.api.v1.api import api_router as api_v1_router
from mindloom.app.middleware.error_handling import http_error_handler

app = FastAPI(
    title="Mindloom API",
    version="0.1.0",
    description="API for managing Mindloom Agents, Teams, and Runs.",
)

# Add the custom error handling middleware
app.add_middleware(http_error_handler)

@app.get("/health", tags=["Health"])
async def health_check():
    """Check the health of the API."""
    return {"status": "ok"}

# Include the v1 API router
app.include_router(api_v1_router, prefix="/api/v1")

# Placeholder for future API routers
# from app.api.v1 import api_router
# app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    # This is for development run only
    # For production, use a process manager like Gunicorn with Uvicorn workers
    uvicorn.run("mindloom.main:app", host="0.0.0.0", port=8000, reload=True, app_dir="src")