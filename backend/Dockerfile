# Use an official Python runtime as a parent image
FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UV_SYSTEM_PYTHON 1 # Use the system python provided by the base image

# Install uv
RUN pip install uv

# Set the working directory in the container
WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Copy the rest of the application code
COPY ./ /app/

# Copy the entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Install dependencies using uv
# --system flag ensures it installs into the main site-packages
RUN uv sync

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Use --host 0.0.0.0 to make it accessible from outside the container
ENTRYPOINT ["/app/entrypoint.sh"]