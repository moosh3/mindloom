#!/bin/bash

# Use 'uv run' to execute uvicorn within the correct environment
# Pass arguments like --log-level directly to uvicorn
uv run uvicorn mindloom.main:app --host 0.0.0.0 --port 8000 --log-level info --app-dir ./src
