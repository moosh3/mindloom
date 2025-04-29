# Mindloom - Actionable Project Tasks

## Phase 1: MVP Backend (P0) - ETA: 2 days

### Infrastructure Setup
- [x] Create Docker configuration for development environment
- [x] Set up PostgreSQL database container
- [x] Configure Redis for pub/sub and caching
- [x] Create initial Kubernetes Helm chart structure

### Database Implementation
- [x] Create database schema for Users table
- [x] Create database schema for Agents table
- [x] Create database schema for Teams table
- [x] Create database schema for Runs table
- [x] Create schema for agent_variables and agent_schedules
- [x] Create schema for team_agents association
- [x] Create schema for run_logs and run_artifacts
- [x] Write database migration scripts
- [x] Implement ORM models for all database tables
- [x] Create database connection pool and configuration

### Authentication System
- [x] Implement JWT token generation and validation
- [x] Create user registration endpoint
- [x] Create user login endpoint
- [x] Implement role-based access control (RBAC)
- [x] Add department association to user profiles
- [x] Create authentication middleware for API routes
- [x] Implement password hashing and security measures
- [x] Set up JWT refresh token mechanism

### Core API Development
- [x] Create FastAPI project structure
- [x] Set up async request handling
- [x] Implement Agent CRUD endpoints
- [x] Implement Team CRUD endpoints
- [x] Create Run management endpoints
- [x] Add content bucket management API
- [ ] Create streaming response endpoints
- [x] Add data validation for all API requests
- [x] Implement error handling middleware
- [x] Create OpenAPI documentation

### Service Layer & Agent/Team Execution
- [x] AgentService: Refine dynamic instantiation of Agno Agent components (Model, Tools, Knowledge, Storage) based on DB config.
- [x] TeamService: Refine dynamic instantiation of Agno Team (Leader Model, Member Agents via AgentService, Knowledge, Storage).
- [x] Tool Handling: Enhance `AgentService._create_tools` for robust mapping and configuration of available tools.
- [x] Knowledge Base: Finalize knowledge base creation (`AgentService._create_knowledge`) including path resolution/content loading.
- [x] Storage: Solidify agent/team run storage configuration (`AgentService._create_storage`).
- [x] Run Execution: Implement core logic for executing agent/team runs (e.g., in `runs.py` endpoint or a dedicated run manager) using AgentService and TeamService.
- [x] Run Execution: Backend logic for `/run` endpoint implemented (incl. error handling).
- [x] Streaming: Add response streaming capabilities to the run execution logic and API endpoints.
- [x] Streaming: Backend API endpoint (`/run`) now streams responses (`application/x-ndjson`). Frontend implementation needed.
- [ ] Context/Memory: Ensure Agno context window and memory parameters (history, etc.) are correctly configured via services.
- [x] Error Handling: Implement error handling and status updates within the run execution logic (backend done).
- [ ] Structured Output: Define and handle structured output requirements (likely via Agno Tools or agent instructions).

## Phase 2: Frontend v2 (P1) - ETA: 2 days

### Authentication UI
- [ ] Create login page
- [ ] Build registration page
- [ ] Implement JWT token management in frontend
- [ ] Add department selection during signup
- [ ] Create user profile page
- [ ] Add "forgot password" functionality
- [ ] Implement session management
- [ ] Add logout functionality

### Agent Management UI
- [x] Create agent listing page with filtering and search
- [x] Build agent creation form
- [ ] Implement agent template selection interface
- [x] Create tool selection and configuration UI
- [x] Build variable definition interface
- [ ] Add agent scheduling options
- [x] Create agent editing functionality
- [ ] Implement form validation
- [ ] Add success/error feedback

### Team Management UI
- [x] Create team listing page
- [x] Build team creation interface
- [x] Implement agent selection for teams
- [ ] Add team type selection (Route, Coordinate, Collaborate)
- [ ] Create team variables configuration
- [ ] Implement team editing functionality
- [ ] Add validation for team configuration
- [ ] Create team details view

### Run Management UI
- [ ] Create run history/listing page
- [ ] Build run details view
- [ ] Implement live streaming log display
- [ ] Create run artifact download functionality
- [ ] Add run status indicators
- [ ] Implement run start/stop controls
- [ ] Create variable input interface for run initialization
- [ ] Build run metrics visualization

### Content Bucket Management
- [ ] Create content bucket listing page
- [ ] Build content bucket creation interface
- [ ] Implement file upload for content buckets
- [ ] Add content bucket association to agents/teams
- [ ] Create content bucket details view
- [ ] Add content search capability
- [ ] Implement file type validation

## Phase 3: Beta Testing and Hardening (P1) - ETA: 2 days

### Security Hardening
- [ ] Implement TLS for all communications
- [ ] Add at-rest encryption for sensitive data
- [ ] Create security scanning in CI/CD pipeline
- [ ] Implement rate limiting
- [ ] Add input sanitization for all user inputs
- [ ] Set up authentication monitoring
- [ ] Create audit logging for all sensitive operations
- [ ] Ensure proper isolation between tenants

### Performance Optimization
- [ ] Implement database query optimization
- [ ] Add Redis caching for frequently accessed data
- [ ] Create database connection pooling
- [ ] Optimize API response times
- [ ] Implement lazy loading for frontend components
- [ ] Add database indexing for performance
- [ ] Setup load testing with k6
- [ ] Optimize streaming response handling

### Integration Testing
- [ ] Create end-to-end tests for user journeys
- [ ] Add API contract tests
- [ ] Implement database integration tests
- [ ] Create frontend component tests
- [ ] Add frontend E2E tests with Cypress
- [ ] Implement LLM integration tests
- [ ] Create tool execution tests

### Deployment Pipeline
- [ ] Configure CI/CD with GitHub Actions
- [ ] Set up containerized builds
- [ ] Create Kubernetes deployment manifests
- [ ] Implement blue/green deployment strategy
- [ ] Add automated testing in pipeline
- [ ] Create staging environment
- [ ] Implement deployment verification tests
- [ ] Add rollback capabilities

### Monitoring and Observability
- [ ] Set up structured JSON logging
- [ ] Implement API metrics collection
- [ ] Create dashboard for system metrics
- [ ] Add business metrics tracking
- [ ] Set up alerting for critical issues
- [ ] Implement distributed tracing
- [ ] Create error reporting system
- [ ] Add user activity analytics

## Phase 4: Second Milestone Features (P2) - Future Implementation

### Agent Workflow Implementation
- [ ] Create database schema for workflows
- [ ] Implement workflow API endpoints
- [ ] Build workflow graph builder UI
- [ ] Create node types (Agent, Team, Tool, Manual)
- [ ] Implement workflow execution engine
- [ ] Add workflow state management
- [ ] Create workflow monitoring interface
- [ ] Implement manual intervention points

### Agent Inbox Implementation
- [ ] Create database schema for inbox messages
- [ ] Implement inbox API endpoints
- [ ] Build inbox UI resembling an email interface
- [ ] Add notification system for new messages
- [ ] Create message categorization (Task Clarification, Review Request, Approval)
- [ ] Implement message action capabilities
- [ ] Add message search and filtering
- [ ] Create message threading for conversations

### Third-Party Integration Expansion
- [ ] Implement GitHub integration
- [ ] Add JIRA integration
- [ ] Create ServiceNow integration
- [ ] Build credential management system
- [ ] Add OAuth flows for service connections
- [ ] Create integration testing frameworks
- [ ] Implement integration error handling
- [ ] Add integration usage analytics

### Advanced Analytics
- [ ] Create admin analytics dashboard
- [ ] Implement usage reporting
- [ ] Add cost tracking per agent/team
- [ ] Create success rate monitoring
- [ ] Implement performance metrics
- [ ] Add user adoption analytics
- [ ] Create export capabilities for reports
- [ ] Build custom report generation

## Kubernetes Agent Execution Tasks

- [ ] **Database:**
    - [ ] Replace in-memory `db_runs` with a persistent database (e.g., PostgreSQL using SQLAlchemy) in `runs.py`.
    - [ ] Implement database session setup (`get_db_session`) in `run_executor.py` using `DATABASE_URL`.
    - [ ] Implement logic to fetch the `Run` object from the DB in `run_executor.py`.
    - [ ] Implement logic to update `Run` status and timestamps (`RUNNING`, `COMPLETED`, `FAILED`) in the DB within `run_executor.py`.
    - [ ] Implement logic to store run output/error in the DB within `run_executor.py`.
- [ ] **Kubernetes & Execution:**
    - [ ] Define actual `KUBERNETES_EXECUTOR_IMAGE` name in settings and build the image using the Dockerfile.
    - [ ] Define resource requests/limits for the executor pod in `runs.py`.
    - [ ] Add `imagePullSecrets` to pod template in `runs.py` if using a private container registry.
    - [ ] Implement proper logging within `run_executor.py`.
    - [ ] Instantiate actual `AgentService`/`TeamService` in `run_executor.py` (likely requiring the DB session).
    - [ ] Implement fetching of runnable details (Agent/Team config) in `run_executor.py` using services.
    - [ ] Import and instantiate `RedisMemoryDb` correctly in `run_executor.py` using `REDIS_URL` and team ID.
    - [ ] Import and instantiate `Agno` `AgentRunner` in `run_executor.py` with runnable config and memory.
    - [ ] Replace placeholder agent execution (`execute_agent`) with the actual call to `runner.run()` in `run_executor.py`.
    - [ ] Ensure Kubernetes RBAC allows the API service account to create Jobs.
- [ ] **Configuration & Validation:**
    - [ ] Validate `runnable_id` exists using services in `runs.py` (optional but recommended).
    - [ ] Ensure all necessary settings (`KUBERNETES_NAMESPACE`, `KUBERNETES_EXECUTOR_IMAGE`, `SQLALCHEMY_DATABASE_URI`, `REDIS_URL`) are present in `settings.py`.
    - [ ] Handle passing sensitive information (like API keys) to the executor pod securely (e.g., via Kubernetes Secrets instead of plain env vars).