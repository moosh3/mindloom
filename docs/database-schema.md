# Database Schema

## Core Tables

### users
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

### agents
```sql
CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  icon TEXT NOT NULL,
  category TEXT NOT NULL,
  instructions TEXT,
  is_custom BOOLEAN DEFAULT false,
  user_id UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_agents_category ON agents(category);
```

### agent_variables
```sql
CREATE TABLE agent_variables (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(id),
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  value TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_variables_agent_id ON agent_variables(agent_id);
```

### agent_schedules
```sql
CREATE TABLE agent_schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(id),
  enabled BOOLEAN DEFAULT false,
  frequency TEXT NOT NULL,
  interval INTEGER NOT NULL,
  time TEXT,
  days INTEGER[],
  date INTEGER,
  timezone TEXT NOT NULL,
  last_run TIMESTAMPTZ,
  next_run TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_schedules_agent_id ON agent_schedules(agent_id);
CREATE INDEX idx_agent_schedules_next_run ON agent_schedules(next_run);
```

### teams
```sql
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  type TEXT NOT NULL CHECK (type IN ('route', 'coordinate', 'collaborate')),
  user_id UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_teams_user_id ON teams(user_id);
```

### team_agents
```sql
CREATE TABLE team_agents (
  team_id UUID NOT NULL REFERENCES teams(id),
  agent_id UUID NOT NULL REFERENCES agents(id),
  position INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (team_id, agent_id)
);

CREATE INDEX idx_team_agents_team_id ON team_agents(team_id);
CREATE INDEX idx_team_agents_agent_id ON team_agents(agent_id);
```

### runs
```sql
CREATE TABLE runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN ('agent', 'team')),
  target_id UUID NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  triggered_by_id UUID NOT NULL REFERENCES users(id),
  input JSONB,
  output JSONB,
  error TEXT,
  duration INTEGER,
  resource_usage JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_runs_target_id ON runs(target_id);
CREATE INDEX idx_runs_triggered_by_id ON runs(triggered_by_id);
CREATE INDEX idx_runs_status ON runs(status);
```

### run_logs
```sql
CREATE TABLE run_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL REFERENCES runs(id),
  message TEXT NOT NULL,
  level TEXT NOT NULL DEFAULT 'info',
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_run_logs_run_id ON run_logs(run_id);
CREATE INDEX idx_run_logs_timestamp ON run_logs(timestamp);
```

### run_artifacts
```sql
CREATE TABLE run_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL REFERENCES runs(id),
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  size INTEGER NOT NULL,
  url TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_run_artifacts_run_id ON run_artifacts(run_id);
```

### conversations
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  agent_id UUID NOT NULL REFERENCES agents(id),
  title TEXT NOT NULL,
  last_message TEXT,
  last_message_time TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
```

### messages
```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id),
  content TEXT NOT NULL,
  sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'agent')),
  attachments JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

## Row Level Security Policies

### users
```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own data"
  ON users
  FOR SELECT
  TO authenticated
  USING (auth.uid() = id);
```

### agents
```sql
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can CRUD own agents"
  ON agents
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id);
```

### teams
```sql
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can CRUD own teams"
  ON teams
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id);
```

### runs
```sql
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own runs"
  ON runs
  FOR SELECT
  TO authenticated
  USING (auth.uid() = triggered_by_id);
```

### conversations
```sql
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can CRUD own conversations"
  ON conversations
  FOR ALL
  TO authenticated
  USING (auth.uid() = user_id);
```

## Relationships

- User has many Agents
- User has many Teams
- User has many Conversations
- Agent has many Variables
- Agent has one Schedule
- Agent belongs to many Teams
- Team has many Agents
- Run has many Logs
- Run has many Artifacts
- Conversation has many Messages
- Conversation belongs to User and Agent

## Indexes

- Email lookup for users
- Category filtering for agents
- User relationship lookups
- Timestamp-based sorting
- Foreign key relationships

## Constraints

- Valid team types (route, coordinate, collaborate)
- Valid run status (running, completed, failed)
- Valid message sender types (user, agent)
- Required fields validation
- Foreign key integrity
- Unique email addresses