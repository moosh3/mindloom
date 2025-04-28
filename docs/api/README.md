# API Reference

## Authentication

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response 200:
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "id": "string",
    "email": "string",
    "name": "string"
  }
}
```

### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}

Response 201:
{
  "id": "string",
  "email": "string",
  "name": "string"
}
```

## Agents

### List Agents
```http
GET /api/agents
Authorization: Bearer <token>

Response 200:
{
  "agents": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "icon": "string",
      "category": "string",
      "created_at": "string"
    }
  ],
  "total": 0,
  "page": 0,
  "per_page": 0
}
```

### Create Agent
```http
POST /api/agents
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "icon": "string",
  "category": "string",
  "instructions": "string",
  "variables": [
    {
      "name": "string",
      "description": "string"
    }
  ],
  "schedule": {
    "enabled": boolean,
    "frequency": "string",
    "interval": number
  }
}

Response 201:
{
  "id": "string",
  "name": "string",
  "description": "string",
  "icon": "string",
  "category": "string",
  "created_at": "string"
}
```

## Teams

### List Teams
```http
GET /api/teams
Authorization: Bearer <token>

Response 200:
{
  "teams": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "type": "route" | "coordinate" | "collaborate",
      "agents": [
        {
          "id": "string",
          "name": "string"
        }
      ],
      "created_at": "string"
    }
  ]
}
```

### Create Team
```http
POST /api/teams
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "type": "route" | "coordinate" | "collaborate",
  "agents": ["string"]
}

Response 201:
{
  "id": "string",
  "name": "string",
  "description": "string",
  "type": "string",
  "created_at": "string"
}
```

## Runs

### List Runs
```http
GET /api/runs
Authorization: Bearer <token>

Response 200:
{
  "runs": [
    {
      "id": "string",
      "type": "agent" | "team",
      "name": "string",
      "status": "running" | "completed" | "failed",
      "start_time": "string",
      "end_time": "string",
      "triggered_by": {
        "id": "string",
        "name": "string"
      }
    }
  ],
  "total": 0,
  "page": 0,
  "per_page": 0
}
```

### Start Run
```http
POST /api/runs
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "agent" | "team",
  "target_id": "string",
  "variables": {
    "string": "string"
  },
  "stream_logs": boolean,
  "scheduled_time": "string"
}

Response 201:
{
  "id": "string",
  "status": "running",
  "start_time": "string"
}
```