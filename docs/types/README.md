# Type Definitions

## Core Types

### User
```typescript
interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
}
```

### Agent
```typescript
interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: AgentCategory;
  isCustom?: boolean;
  createdAt?: Date;
  schedule?: Schedule;
  variables?: AgentVariable[];
  instructions?: string;
}
```

### Team
```typescript
interface Team {
  id: string;
  name: string;
  description: string;
  type: 'route' | 'coordinate' | 'collaborate';
  agents: Agent[];
  createdAt: Date;
}
```

### Run
```typescript
interface Run {
  id: string;
  startTime: Date;
  endTime?: Date;
  triggeredBy: {
    id: string;
    name: string;
    avatar?: string;
  };
  status: 'running' | 'completed' | 'failed';
  duration?: number;
  logs: string[];
  input: Record<string, any>;
  output?: Record<string, any>;
  artifacts: RunArtifact[];
  resourceUsage?: {
    cpuTime: number;
    memoryUsage: number;
    apiCalls: number;
  };
}
```

### Schedule
```typescript
interface Schedule {
  enabled: boolean;
  frequency: 'hourly' | 'daily' | 'weekly' | 'monthly';
  interval: number;
  time?: string;
  days?: number[];
  date?: number;
  timezone: string;
  lastRun?: Date;
  nextRun?: Date;
}
```

## UI Types

### FilterOption
```typescript
interface FilterOption {
  id: string;
  label: string;
  value: string;
}
```

### TabOption
```typescript
interface TabOption {
  id: string;
  label: string;
  count?: number;
}
```