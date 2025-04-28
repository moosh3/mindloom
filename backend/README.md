# Mindloom Backend API

This directory contains the FastAPI backend service for the Mindloom platform.

## Setup

1.  **Install Dependencies:**
    ```bash
    # Make sure you have uv installed (pipx install uv)
    cd backend
    uv sync
    ```

2.  **Run Development Server:**
    ```bash
    # From the backend directory
    uvicorn mindloom.main:app --host 0.0.0.0 --port 8000 --reload --app-dir src
    ```
    Alternatively, you can run the `main.py` script directly (less common for FastAPI apps):
    ```bash
    # From the backend directory
    python src/mindloom/main.py
    ```

3.  **Access API Docs:**
    Open your browser to [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI or [http://localhost:8000/redoc](http://localhost:8000/redoc) for ReDoc.

## Project Structure

```
backend/
├── src/
│   └── mindloom/        # Main application package
│       ├── __init__.py
│       ├── main.py        # FastAPI application entry point
│       └── app/           # API modules (routes, models, services)
├── .gitignore
├── pyproject.toml     # Project metadata and dependencies (uv)
├── README.md          # This file
├── uv.lock            # Pinned dependency versions
└── .venv/             # Virtual environment (managed by uv)