# MindLoom Agent UI

## Description

MindLoom Agent UI is a web-based platform for creating, managing, and running AI agents and teams built using the Agno AI library. It provides a user-friendly interface to interact with agents, execute tasks, and view results in real-time.

The backend is built with FastAPI and leverages PostgreSQL for persistent storage, Redis for caching and real-time messaging (Pub/Sub), and Kubernetes for scalable execution of agent runs.

The frontend (planned) will be built using React and TypeScript.

## Technology Stack

*   **Backend:** Python, FastAPI, SQLAlchemy (asyncpg), Pydantic
*   **Database:** PostgreSQL
*   **Caching/Messaging:** Redis
*   **Execution Environment:** Kubernetes
*   **Core AI Library:** Agno AI
*   **Frontend (Planned):** React, TypeScript, Vite, Tailwind CSS, Zustand, Lucide React
*   **CI/CD:** (To be defined - likely GitHub Actions)

## Key Features

*   **Agent & Team Management:** Create, configure, and manage Agno Agents and Teams through a REST API.
*   **Run Execution:** Initiate agent/team runs via API, executed as isolated Kubernetes Jobs.
*   **Real-time Log Streaming:** View execution logs in real-time via WebSocket connection.
*   **Real-time Result Streaming:** Receive intermediate and final results from runs in real-time via Server-Sent Events (SSE).
*   **Persistent Storage:** Agent/Team configurations and run history stored in PostgreSQL.
*   **Dynamic Configuration:** Supports dynamic configuration of models, tools, knowledge bases, and memory for agents/teams.

## Setup Instructions

*(Instructions below are placeholders and need refinement based on actual setup steps)*

### Prerequisites

*   Python 3.10+
*   Docker & Docker Compose (or Minikube/Kubernetes cluster access)
*   `kubectl` configured for your cluster
*   Access to a PostgreSQL database
*   Access to a Redis instance

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd agentui/backend
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables:**
    *   Copy `.env.example` to `.env`.
    *   Update `.env` with your database URL, Redis URL, Kubernetes namespace, JWT secret, etc.
5.  **Run database migrations (if using Alembic):**
    ```bash
    alembic upgrade head
    ```

### Frontend Setup (Planned)

1.  Navigate to the frontend directory:
    ```bash
    cd ../frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```

## How to Run

### Running the Backend Locally

```bash
cd backend
# Ensure PostgreSQL and Redis are running and accessible
# Ensure your .env file is configured

# Start the FastAPI server
uvicorn mindloom.main:app --reload --host 0.0.0.0 --port 8000
```

### Running with Docker Compose (Example - Needs `docker-compose.yml`)

```bash
# Ensure docker-compose.yml is present and configured
docker-compose up --build
```

### Running via Kubernetes

1.  Build and push Docker images for the backend.
2.  Apply Kubernetes manifests (deployment, service, ingress, etc.).

## Development

*   **Branching:** Follow standard Gitflow or similar branching strategy.
*   **Testing:** (Testing strategy to be defined - e.g., Pytest for backend, Jest/RTL for frontend).
*   **Linting/Formatting:** Use `black`, `ruff`, `prettier` (for frontend) to maintain code style.

## Contributing

(Contribution guidelines to be defined)
