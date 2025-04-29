#!/bin/bash

# Script to test creating a simple agent and starting a run via the API

set -e # Exit immediately if a command exits with a non-zero status.
set -u # Treat unset variables as an error.

# --- Configuration ---
API_BASE_URL="http://localhost:8000/api/v1"
AGENT_NAME="Test Agent $(date +%s)" # Unique name using timestamp
AGENT_DESCRIPTION="A simple agent created via script for testing."
RUN_INPUT_MESSAGE="Hello, Agent! How are you today?"

# Minimal model config for OpenAI provider (backend expects lowercase provider and a params block)
MODEL_CONFIG='{
  "provider": "openai",
  "params": {
    "model_name": "gpt-4o",
    "config_overrides": {}
  }
}'

# --- Auth Credentials (adjust or export as env vars) ---
USER_EMAIL="${USER_EMAIL:-admin@example.com}"
USER_PASSWORD="${USER_PASSWORD:-password1234}"

# --- Script --- 

echo "--- Authenticating as ${USER_EMAIL} ---"

# OAuth2PasswordRequestForm uses application/x-www-form-urlencoded
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${USER_EMAIL}&password=${USER_PASSWORD}" \
  "${API_BASE_URL}/auth/login")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
  echo "Error: Failed to obtain access token. Response was: $TOKEN_RESPONSE"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer ${ACCESS_TOKEN}"

echo "Successfully authenticated. Access token obtained."

echo "\n--- Creating Agent: ${AGENT_NAME} --- "

# Prepare agent creation payload
AGENT_PAYLOAD=$(cat <<EOF
{
  "name": "${AGENT_NAME}",
  "description": "${AGENT_DESCRIPTION}",
  "model_config": ${MODEL_CONFIG},
  "tool_configs": [],
  "knowledge_base_configs": [],
  "storage_config": null, 
  "team_id": null 
}
EOF
)

# Make API call to create agent
CREATE_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/agents/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "${AGENT_PAYLOAD}")

# Check if agent creation was successful and extract ID
AGENT_ID=$(echo "${CREATE_RESPONSE}" | jq -r '.id')

if [ -z "${AGENT_ID}" ] || [ "${AGENT_ID}" == "null" ]; then
  echo "Error: Failed to create agent or extract agent ID."
  echo "Response: ${CREATE_RESPONSE}"
  exit 1
fi

echo "Agent created successfully! Agent ID: ${AGENT_ID}"

echo "
--- Starting Run for Agent ID: ${AGENT_ID} ---"

# Prepare run creation payload (align with RunCreate schema)
RUN_PAYLOAD=$(cat <<EOF
{
  "runnable_id": "${AGENT_ID}",
  "runnable_type": "agent",
  "input_variables": {
    "message": "${RUN_INPUT_MESSAGE}"
  }
}
EOF
)

# Make API call to start the run (response will be streaming)
# We use -N to disable buffering and see stream output immediately if desired,
# but for just starting it, a simple POST is fine.
# The --max-time flag prevents curl from hanging indefinitely on the stream.
RUN_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/runs/" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "$AUTH_HEADER" \
  -d "${RUN_PAYLOAD}" \
  --max-time 5)

# Basic check if the request seemed to start (might not capture full stream)
if [[ "${RUN_RESPONSE}" == *"event: result"* ]] || [[ "${RUN_RESPONSE}" == *"event: end"* ]] || [[ -z "${RUN_RESPONSE}" ]]; then
    # Check for specific stream events or empty response (if --max-time cut it short)
    echo "Run started successfully (or request sent). Check backend logs/stream for details."
    echo "Initial Response Snippet: ${RUN_RESPONSE:0:200}..."
else
    echo "Warning: Run start request might have failed or response format unexpected."
    echo "Response: ${RUN_RESPONSE}"
    # Continue anyway, but log warning
fi

echo "
--- Workflow Script Completed ---"
