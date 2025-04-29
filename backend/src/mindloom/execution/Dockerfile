# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by some Python packages
# Example: build-essential for C extensions, libpq-dev for psycopg2
# Adjust as needed based on your requirements.txt
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip

# Copy uv lock file and pyproject.toml (relative to backend context)
COPY uv.lock /app/uv.lock
COPY pyproject.toml /app/pyproject.toml

# Copy the ENTIRE src directory into the container (relative to backend context)
# This creates /app/src/mindloom, which uv sync seems to expect based on pyproject.toml
COPY src /app/src

# Install uv
RUN pip install --no-cache-dir uv

# Sync dependencies directly from the lock file in the current directory (/app)
# This will also install the local mindloom package using the copied source
RUN uv sync --no-cache

# The Kubernetes job definition specifies the command,
# so CMD/ENTRYPOINT here is mostly for documentation or testing locally.
# CMD ["python", "/app/mindloom/execution/run_executor.py"]
