from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional, Any, AsyncGenerator
import uuid
from datetime import datetime
import asyncio
import json # For serializing input_data
import os # For potential env vars
import logging # Add logging

from kubernetes import client, config
from sqlalchemy.ext.asyncio import AsyncSession # Import AsyncSession

from mindloom.app.models.run import Run, RunCreate, RunStatus
from mindloom.dependencies import get_current_user
from mindloom.app.models.user import User
from mindloom.services.agents import AgentService # Keep for potential validation
from mindloom.services.teams import TeamService     # Keep for potential validation
from mindloom.core.config import settings
from mindloom.db.session import get_async_db_session
from mindloom.services.runs import run_service # Import the service instance
from mindloom.app.models.run import Run as RunSchema # Import Pydantic schema
from mindloom.services import redis as redis_service # Import Redis service

# --- Kubernetes Configuration --- 
# Load Kubernetes configuration
try:
    if os.getenv('KUBERNETES_SERVICE_HOST'):
        config.load_incluster_config()
        print("Loaded in-cluster Kubernetes config")
    else:
        config.load_kube_config()
        print("Loaded local Kube config")
    K8S_BATCH_V1_API = client.BatchV1Api()
    K8S_NAMESPACE = settings.KUBERNETES_NAMESPACE # Expect KUBERNETES_NAMESPACE in settings
    print(f"Kubernetes client initialized for namespace: {K8S_NAMESPACE}")
except Exception as e:
    print(f"Error loading Kubernetes config: {e}. Job creation will fail.")
    K8S_BATCH_V1_API = None
    K8S_NAMESPACE = 'default' # Fallback or raise?

router = APIRouter(dependencies=[Depends(get_current_user)])

# Get a logger instance (can be configured further in main app setup)
logger = logging.getLogger(__name__)

async def _stream_run_results(run_id: str) -> AsyncGenerator[str, None]:
    """Async generator to subscribe to Redis and yield SSE messages for a run."""
    channel_name = f"run_results:{run_id}"
    pubsub = None
    try:
        # Use the existing redis_service for connection
        pubsub = redis_service.redis.pubsub()
        await pubsub.subscribe(channel_name)
        logger.info(f"Subscribed to Redis channel: {channel_name}")

        while True:
            # Listen for messages with a timeout to allow checking connection
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None and message["type"] == "message":
                try:
                    # Assuming message['data'] is the JSON string from run_executor
                    data_str = message['data'] # Already decoded by redis_service pool
                    # Format as SSE message
                    sse_message = f"data: {data_str}\n\n"
                    yield sse_message

                    # Check if this is the end message
                    try:
                        data_obj = json.loads(data_str)
                        if isinstance(data_obj, dict) and data_obj.get("event") == "end":
                            logger.info(f"Received end event for {channel_name}, closing stream.")
                            break # Exit the loop, generator finishes
                    except json.JSONDecodeError:
                        pass # Ignore if data isn't valid JSON for the 'end' check

                except Exception as e:
                    logger.error(f"Error processing message from {channel_name}: {e}", exc_info=True)
                    # Optional: yield an error event to the client
                    yield f"event: error\ndata: {{\"error\": \"Error processing stream message\"}}\n\n"

            # Optional: Add a small sleep if no message to prevent tight loop on timeout
            elif message is None:
                 await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        logger.info(f"Run result streaming cancelled for {channel_name}.")
    except Exception as e:
        logger.error(f"Error during Redis subscription/listen for {channel_name}: {e}", exc_info=True)
        # Optional: yield an error event to the client
        try:
            yield f"event: error\ndata: {{\"error\": \"Stream disconnected due to server error\"}}\n\n"
        except Exception:
            pass # Ignore if yield fails after error
    finally:
        logger.info(f"Cleaning up stream for {channel_name}.")
        if pubsub:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
                logger.info(f"Unsubscribed and closed pubsub for {channel_name}")
            except Exception as unsub_err:
                logger.error(f"Error unsubscribing/closing pubsub for {channel_name}: {unsub_err}")


@router.post(
    "/", 
    status_code=status.HTTP_200_OK, 
    tags=["Runs"],
    summary="Start a run and stream results (SSE)",
    response_description="A stream of Server-Sent Events containing run results."
)
async def create_run(
    run_in: RunCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db_session) # Inject DB session
) -> StreamingResponse:
    """
    Start a new run for an agent or team by launching a Kubernetes Job.
    Returns a Server-Sent Events stream with run results.
    """
    # Basic validation (can be enhanced later)
    if run_in.runnable_type not in ['agent', 'team']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid runnable_type. Must be 'agent' or 'team'.")

    # TODO: Validate runnable_id exists using AgentService/TeamService if needed

    # 1. Create Run record in DB with PENDING status
    try:
        db_run = await run_service.create_run(
            db=db,
            runnable_id=run_in.runnable_id,
            runnable_type=run_in.runnable_type,
            input_variables=run_in.input_variables,
            # user_id=current_user.id # Pass user ID if available from auth
        )
        run_id = db_run.id # Use the ID generated by the database
        print(f"Created Run {run_id} in database with status PENDING.")
    except Exception as e:
         # Log the error appropriately
        print(f"Error creating run record in database: {e}")
        raise HTTPException(status_code=500, detail="Failed to create run record in database.")


    if not K8S_BATCH_V1_API:
        # Update status to FAILED if K8s client failed to init
        await run_service.update_run_status(
            db=db,
            run_id=run_id,
            status=RunStatus.FAILED,
            output_data={"error": "Kubernetes client not initialized. Cannot create job."}
        )
        print(f"Marked Run {run_id} as FAILED in database due to K8s client initialization error.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kubernetes client not available. Cannot schedule run."
        )

    # 2. Define Kubernetes Job
    job_name = f"mindloom-run-{run_id}"
    namespace = settings.KUBERNETES_NAMESPACE

    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password = os.getenv('REDIS_PASSWORD', '')
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"

    # Prepare environment variables for the executor pod
    env_vars = [
        client.V1EnvVar(name="RUN_ID", value=str(run_id)),
        client.V1EnvVar(name="RUNNABLE_TYPE", value=run_in.runnable_type),
        client.V1EnvVar(name="RUNNABLE_ID", value=str(run_in.runnable_id)),
        client.V1EnvVar(name="INPUT_DATA", value=json.dumps(run_in.input_variables or {})),
        # Assuming DATABASE_URL and REDIS_URL are needed by the executor
        # These should ideally come from Secrets or a ConfigMap in a real setup
        client.V1EnvVar(name="DATABASE_URL", value=settings.DATABASE_URL.unicode_string()),
        client.V1EnvVar(name="REDIS_URL", value=redis_url),
        # Add other necessary env vars (e.g., API keys via Secrets)
        # client.V1EnvVar(name="OPENAI_API_KEY", value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name="mindloom-secrets", key="openai-api-key"))),
    ]

    # Define the container for the Job
    container = client.V1Container(
        name="run-executor",
        image=settings.KUBERNETES_EXECUTOR_IMAGE, # Use image from settings
        command=["python", "/app/mindloom/execution/run_executor.py"], # Command to run the script
        env=env_vars,
        image_pull_policy="IfNotPresent", # Or "Always" if using :latest tag
        # Add resource requests/limits
        # resources=client.V1ResourceRequirements(
        #     requests={"cpu": "100m", "memory": "256Mi"},
        #     limits={"cpu": "500m", "memory": "512Mi"},
        # ),
    )

    # Define the Pod template spec
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "mindloom-run-executor", "run_id": str(run_id)}),
        spec=client.V1PodSpec(
            restart_policy="Never", # Jobs should not restart pods on failure
            containers=[container],
            # Add imagePullSecrets if using a private registry
            # image_pull_secrets=[client.V1LocalObjectReference(name="my-registry-secret")]
            # Consider serviceAccountName if specific permissions are needed for the pod
            # service_account_name="mindloom-executor-sa"
        ),
    )

    # Define the Job spec
    job_spec = client.V1JobSpec(
        template=template,
        backoff_limit=1, # Number of retries before marking job as failed
        ttl_seconds_after_finished=3600 # Auto-cleanup finished jobs after 1 hour
    )

    # Define the Job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name, labels={"app": "mindloom-run", "run_id": str(run_id)}),
        spec=job_spec,
    )

    # 3. Create the Kubernetes Job
    try:
        print(f"Creating Kubernetes Job '{job_name}' in namespace '{namespace}'...")
        job_response = K8S_BATCH_V1_API.create_namespaced_job(body=job, namespace=namespace)
        print(f"Kubernetes Job created successfully. Job status: {job_response.status}")
    except client.ApiException as e:
        print(f"Error creating Kubernetes Job: {e.status} - {e.reason}")
        print(f"Body: {e.body}")
        # Attempt to mark the DB run as FAILED if Job creation fails
        try:
            await run_service.update_run_status(
                db=db,
                run_id=run_id,
                status=RunStatus.FAILED,
                output_data={"error": f"Failed to create Kubernetes Job: {e.reason}"}
            )
            print(f"Marked Run {run_id} as FAILED in database due to Job creation error.")
        except Exception as db_err:
             print(f"Failed to mark Run {run_id} as FAILED after Job creation error: {db_err}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to launch run execution job: {e.reason}",
        )
    except Exception as e:
         # Catch other potential errors during job creation setup
         print(f"Unexpected error preparing or creating Kubernetes Job: {e}")
         # Attempt to mark the DB run as FAILED
         try:
             await run_service.update_run_status(
                 db=db,
                 run_id=run_id,
                 status=RunStatus.FAILED,
                 output_data={"error": f"Unexpected error during Job creation: {e}"}
             )
             print(f"Marked Run {run_id} as FAILED in database due to unexpected Job creation error.")
         except Exception as db_err:
              print(f"Failed to mark Run {run_id} as FAILED after unexpected Job creation error: {db_err}")
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="An unexpected error occurred while launching the run execution job.",
         )


    # Return StreamingResponse
    return StreamingResponse(_stream_run_results(str(run_id)), media_type="text/event-stream")


@router.get("/", response_model=List[RunSchema], tags=["Runs"])
async def read_runs(
    skip: int = 0,
    limit: int = 100,
    runnable_id: Optional[uuid.UUID] = None, # Optional filter by agent/team
    status: Optional[RunStatus] = None       # Optional filter by status
) -> List[Run]:
    """
    Retrieve a list of runs, with optional filtering.
    """
    runs_list = await run_service.get_runs(
        db=get_async_db_session(),
        skip=skip,
        limit=limit,
        runnable_id=runnable_id,
        status=status
    )

    # Apply sorting (e.g., newest first)
    runs_list.sort(key=lambda r: r.created_at, reverse=True)

    return runs_list


@router.get("/{run_id}", response_model=RunSchema, tags=["Runs"])
async def read_run(run_id: uuid.UUID) -> Run:
    """
    Retrieve a specific run by ID.
    """
    run = await run_service.get_run(db=get_async_db_session(), run_id=run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run

# Potential future endpoint: Cancel a run
# @router.post("/{run_id}/cancel", response_model=Run, tags=["Runs"])
# async def cancel_run(run_id: uuid.UUID) -> Run:
#     ...


@router.websocket("/ws/runs/{run_id}/logs")
async def websocket_log_stream(websocket: WebSocket, run_id: uuid.UUID):
    """Provides a WebSocket endpoint to stream logs for a specific run_id."""
    await websocket.accept()
    channel_name = f"run_logs:{run_id}"
    pubsub = None
    redis_client = None
    listener_task = None

    try:
        # Get Redis client and pubsub
        try:
            redis_client = await redis_service.get_client()
            if not redis_client:
                logger.error(f"Could not get Redis client for run {run_id} logs.")
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Redis service not available")
                return
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(channel_name)
            logger.info(f"WebSocket client connected and subscribed to Redis channel: {channel_name}")
        except Exception as e:
            logger.error(f"Error connecting to Redis or subscribing to {channel_name}: {e}", exc_info=True)
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Failed to subscribe to log channel")
            return

        # Task to listen to Redis and forward messages
        async def redis_listener(ws: WebSocket, ps: redis_service.redis.client.PubSub):
            try:
                async for message in ps.listen():
                    if message is not None and message["type"] == "message":
                        try:
                            # Assuming message['data'] is bytes containing JSON string from RedisPubSubHandler
                            log_data_str = message['data'].decode('utf-8')
                            await ws.send_text(log_data_str)
                        except WebSocketDisconnect:
                            logger.info(f"WebSocket client disconnected while sending from {channel_name}.")
                            break # Exit listener loop
                        except Exception as send_err:
                             logger.error(f"Error sending log message via WebSocket for {channel_name}: {send_err}", exc_info=True)
                             break # Exit loop on send error
            except asyncio.CancelledError:
                 logger.info(f"Redis listener task cancelled for {channel_name}.")
            except Exception as listen_err:
                 # Log redis-py specific errors if possible
                 logger.error(f"Error in Redis listener for {channel_name}: {listen_err}", exc_info=True)
                 # Attempt to close WebSocket gracefully on listener error
                 try:
                    await ws.close(code=status.WS_1011_INTERNAL_ERROR, reason="Log stream disconnected")
                 except Exception:
                     pass # Ignore errors during closing
            finally:
                logger.info(f"Redis listener task concluding for {channel_name}.")
                # Ensure unsubscribe happens in the main finally block

        listener_task = asyncio.create_task(redis_listener(websocket, pubsub))

        # Keep connection open by listening for client messages (or disconnect)
        try:
            while True:
                # This will block until data is received or connection is closed by client
                # We don't expect messages from the client, but this detects disconnect
                await websocket.receive_text() 
        except WebSocketDisconnect:
             logger.info(f"WebSocket client initiated disconnect for {channel_name}.")

        # Wait for the listener task to finish if it hasn't already (e.g., if disconnect happened)
        if listener_task and not listener_task.done():
            await listener_task

    except WebSocketDisconnect:
        # This catches disconnects that happen before the receive_text loop starts
        logger.info(f"WebSocket client disconnected early for {channel_name}.")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket endpoint for {channel_name}: {e}", exc_info=True)
        # Attempt to close gracefully
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
    finally:
        logger.info(f"Cleaning up WebSocket connection for {channel_name}.")
        # Cancel the listener task if it's still running
        if listener_task and not listener_task.done():
            listener_task.cancel()
            try:
                await listener_task # Allow cancellation to propagate
            except asyncio.CancelledError:
                pass # Expected
            except Exception as task_wait_err:
                 logger.error(f"Error waiting for cancelled listener task {channel_name}: {task_wait_err}")

        # Unsubscribe and clean up PubSub
        if pubsub:
            try:
                await pubsub.unsubscribe(channel_name)
                # Close the pubsub connection object itself
                await pubsub.close()
                logger.info(f"Unsubscribed and closed pubsub for Redis channel: {channel_name}")
            except Exception as unsub_err:
                logger.error(f"Error unsubscribing/closing pubsub for {channel_name}: {unsub_err}")
        
        # WebSocket should be closed by FastAPI or handled in exception blocks
        logger.info(f"WebSocket cleanup finished for {channel_name}.")
