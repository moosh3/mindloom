# Development Guide

## Code Style Guide

### TypeScript
- Use strict type checking
- Prefer interfaces over types for objects
- Use type inference when possible
- Document complex types

```typescript
// Good
interface User {
  id: string;
  name: string;
  email: string;
}

// Avoid
type User = {
  id: string;
  name: string;
  email: string;
};
```

### React Components
- Use functional components with hooks
- Props should be typed
- Use destructuring for props
- Keep components focused and small

```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  children: React.ReactNode;
  onClick?: () => void;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  children,
  onClick,
}) => {
  return (
    <button
      className={`btn btn-${variant}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};
```

### State Management
- Use Zustand for global state
- Keep state minimal and normalized
- Use local state for UI-only state
- Document store interfaces

```typescript
interface AuthState {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  signIn: async (email, password) => {
    // Implementation
  },
  signOut: async () => {
    // Implementation
  },
}));
```

## Contributing Guidelines

1. **Branch Naming**
   - Feature: `feature/description`
   - Bug fix: `fix/description`
   - Documentation: `docs/description`

2. **Commit Messages**
   - Use present tense
   - Be descriptive
   - Reference issues

   ```
   feat: add team run configuration
   fix: resolve agent selection in teams
   docs: update API documentation
   ```

3. **Pull Requests**
   - Include description of changes
   - Link related issues
   - Add tests if applicable
   - Update documentation

## Testing Procedures

### Unit Tests
```typescript
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    screen.getByText('Click me').click();
    expect(onClick).toHaveBeenCalled();
  });
});
```

### Integration Tests
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { AgentList } from './AgentList';

describe('AgentList', () => {
  it('loads and displays agents', async () => {
    render(<AgentList />);
    
    await waitFor(() => {
      expect(screen.getByText('Q&A Agent')).toBeInTheDocument();
    });
  });
});
```

## Deployment Process

1. **Build**
```bash
npm run build
```

2. **Environment Variables**
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

3. **Database Migrations**
```bash
supabase db push
```

4. **Deploy**
```bash
npm run deploy
```

## Performance Optimization

1. **Code Splitting**
```typescript
const AgentDetail = React.lazy(() => import('./AgentDetail'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <AgentDetail />
    </Suspense>
  );
}
```

2. **Memoization**
```typescript
const MemoizedComponent = React.memo(({ data }) => {
  return <div>{data}</div>;
});
```

3. **Virtual Lists**
```typescript
import { FixedSizeList } from 'react-window';

const VirtualList = ({ items }) => (
  <FixedSizeList
    height={400}
    width={600}
    itemCount={items.length}
    itemSize={50}
  >
    {({ index, style }) => (
      <div style={style}>{items[index]}</div>
    )}
  </FixedSizeList>
);
```