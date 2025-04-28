# Integration Guide

## Getting Started

1. Install the required dependencies:
```bash
npm install @supabase/supabase-js zustand
```

2. Initialize Supabase client:
```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);
```

3. Set up authentication store:
```typescript
import { create } from 'zustand';

interface AuthState {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  signIn: async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
    set({ user: data.user });
  },
  signUp: async (email, password, name) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { name },
      },
    });
    if (error) throw error;
    set({ user: data.user });
  },
  signOut: async () => {
    await supabase.auth.signOut();
    set({ user: null });
  },
}));
```

## Common Use Cases

### Creating an Agent
```typescript
const createAgent = async (agent: Omit<Agent, 'id' | 'createdAt'>) => {
  const { data, error } = await supabase
    .from('agents')
    .insert([agent])
    .select()
    .single();
  
  if (error) throw error;
  return data;
};
```

### Starting a Run
```typescript
const startRun = async (config: {
  type: 'agent' | 'team';
  targetId: string;
  variables: Record<string, string>;
}) => {
  const { data, error } = await supabase
    .from('runs')
    .insert([{
      type: config.type,
      target_id: config.targetId,
      variables: config.variables,
      status: 'running',
      start_time: new Date(),
    }])
    .select()
    .single();
  
  if (error) throw error;
  return data;
};
```

### Streaming Logs
```typescript
const subscribeToLogs = (runId: string, onLog: (log: string) => void) => {
  const subscription = supabase
    .channel(`run-${runId}`)
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'run_logs',
        filter: `run_id=eq.${runId}`,
      },
      (payload) => {
        onLog(payload.new.message);
      }
    )
    .subscribe();

  return () => {
    subscription.unsubscribe();
  };
};
```

## Best Practices

1. **Error Handling**
```typescript
try {
  await createAgent(agentData);
} catch (error) {
  if (error instanceof PostgrestError) {
    // Handle database errors
  } else if (error instanceof AuthError) {
    // Handle authentication errors
  } else {
    // Handle other errors
  }
}
```

2. **Type Safety**
```typescript
// Generate types from database schema
supabase gen types typescript --project-id your-project-id > src/types/supabase.ts

// Use generated types
import { Database } from './types/supabase';
type DbAgent = Database['public']['Tables']['agents']['Row'];
```

3. **Real-time Updates**
```typescript
const subscribeToAgentUpdates = (onUpdate: (agent: Agent) => void) => {
  const subscription = supabase
    .channel('agents')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'agents',
      },
      (payload) => {
        onUpdate(payload.new as Agent);
      }
    )
    .subscribe();

  return () => {
    subscription.unsubscribe();
  };
};
```