# Task List: Implement Real-time Log Streaming for Runs (WebSocket + Redis)

## I. Backend Infrastructure & Setup

- [ ] **Verify/Add Dependencies:**
    - [ ] Ensure `redis` package is in `backend/pyproject.toml` and `backend/uv.lock`.
    - [ ] Ensure WebSocket support (`websockets` package or FastAPI built-in) is available for the FastAPI app.
- [ ] **Redis Client Utility (Optional but Recommended):**
    - [ ] Create/Enhance utility/service (`mindloom/services/redis.py`?) for managing Redis connections and Pub/Sub helpers.

## II. Executor Modifications (`run_executor.py`)

- [x] **Setup Python Logging:**
    - [x] Import `logging`.
    - [x] Configure a basic logger instance.
- [x] **Implement Redis Logging Handler:**
    - [x] Create `RedisPubSubHandler(logging.Handler)` subclass.
    - [x] `__init__`: Connect to Redis (`REDIS_URL`).
    - [x] `emit(self, record)`: Format record, get `run_id`, construct channel name (`run_logs:{run_id}`), `PUBLISH` message to channel. Add error handling.
- [x] **Configure Logger to Use Handler:**
    - [x] Instantiate `RedisPubSubHandler`.
    - [x] Add handler to the logger instance.
    - [x] Set logging level (e.g., `logging.INFO`).
- [x] **Replace `print` with `logging`:**
    - [x] Replace relevant `print()` with `logging.info()`, `logging.warning()`, `logging.error()`, etc.
- [x] **Add Final Status Log:**
    - [x] Ensure a final log message ("Run COMPLETED" / "Run FAILED: [error]") is published before exit.

## III. Update Executor Docker Image

- [x] **Update Dockerfile:** Verify `redis` dependency is installed.
- [x] **Rebuild Docker Image:** Build `mindloom-executor:latest`.
    ```bash
    # From backend directory
    docker build -f src/mindloom/execution/Dockerfile -t mindloom-executor:latest .
    ```
- [x] **Push Image (If necessary):** Push updated image to container registry.

## IV. FastAPI Backend Modifications

- [x] **Create WebSocket Endpoint:**
    - [x] Define route `/{run_id}/logs` (e.g., in `runs.py` or `websockets.py`).
    - [x] Example: `@router.websocket("/ws/runs/{run_id}/logs")`.
- [x] **Implement WebSocket Connection Logic:**
    - [x] `async def websocket_endpoint(websocket: WebSocket, run_id: uuid.UUID)`
    - [x] Accept connection: `await websocket.accept()`.
- [x] **Implement Redis Subscription Logic:**
    - [x] Connect to Redis (use utility if created).
    - [x] Subscribe to channel `f"run_logs:{run_id}"`.
- [x] **Implement Message Forwarding Loop:**
    - [x] Async loop: Listen for messages on Redis channel.
    - [x] On message received: `await websocket.send_text(message)`.
    - [x] Handle Redis/WebSocket errors.
- [x] **Handle WebSocket Disconnection:**
    - [x] Use `try...finally` or `on_disconnect`.
    - [x] Clean up Redis subscription.
- [ ] **(Optional) Handle Historical Logs:** Decide and implement if initial logs should be sent on connect.

## V. Frontend Client Modifications (Conceptual Tasks)

- [ ] **WebSocket Library:** Integrate WebSocket client library.
- [ ] **Initiate Connection:** Connect to `/ws/runs/{run_id}/logs` after starting run.
- [ ] **Receive Messages:** Set up message listener/callback.
- [ ] **Display Logs:** Update UI to show incoming log messages.
- [ ] **Handle Connection State:** Implement UI feedback for connection status (opening, errors, closed).

## VI. Testing

- [ ] **Unit/Integration Tests:** Test Redis handler and WebSocket endpoint logic.
- [ ] **End-to-End Test:** Test the full flow (API -> Job -> Logs -> WebSocket -> Client).

## VII. Additional Tasks

- [x] **Debug Backend Startup Issues (Import errors related to schemas, logging, AsyncSession).**
    - *Note: Backend service is now running successfully via `docker compose up`.*