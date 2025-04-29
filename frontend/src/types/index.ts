export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
}

export interface Agent {
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

export type AgentCategory = 
  | 'customer-service'
  | 'sales'
  | 'engineering'
  | 'support'
  | 'marketing'
  | 'it'
  | 'hr'
  | 'popular';

export interface AgentVariable {
  name: string;
  description: string;
  value?: string;
}

export interface Schedule {
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

export interface Team {
  id: string;
  name: string;
  description: string;
  type: 'route' | 'coordinate' | 'collaborate';
  agents: Agent[];
  createdAt: Date;
}

export interface Run {
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
  error?: string;
  resourceUsage?: {
    cpuTime: number;
    memoryUsage: number;
    apiCalls: number;
  };
}

export interface AgentRun extends Run {
  agentId: string;
  agentName: string;
}

export interface TeamRun extends Run {
  teamId: string;
  teamName: string;
  teamType: Team['type'];
  agentRuns: AgentRun[];
}

export interface FilterOption {
  id: string;
  label: string;
  value: string;
}

export interface TabOption {
  id: string;
  label: string;
  count?: number;
}