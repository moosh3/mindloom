# Project Overview

AgnoAgents is a modern web application for managing AI agents and orchestrating their interactions through teams and workflows.

## Core Features

- **Agent Management**: Create, customize, and deploy AI agents
- **Team Orchestration**: Organize agents into teams with different collaboration patterns
- **Workflow Builder**: Visual interface for creating complex agent workflows
- **Real-time Monitoring**: Track agent and team execution with live logs
- **Content Management**: Organize and share knowledge bases between agents
- **Run History**: Comprehensive history of agent and team executions

## System Architecture

The application follows a modern React-based architecture with the following key components:

- **Frontend**: React + TypeScript + Vite
- **State Management**: Zustand for global state
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Real-time**: Supabase Realtime
- **File Storage**: Supabase Storage

## Tech Stack

- **Core Framework**: React 18.3
- **Build Tool**: Vite 5.4
- **Styling**: Tailwind CSS 3.4
- **Icons**: Lucide React
- **Type Safety**: TypeScript 5.5
- **State Management**: Zustand 4.5
- **API Client**: @supabase/supabase-js 2.39

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set up environment variables:
   ```env
   VITE_SUPABASE_URL=your_supabase_url
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

## Project Structure

```
/
├── docs/                    # Documentation
├── src/
│   ├── components/         # React components
│   │   ├── agents/        # Agent-related components
│   │   ├── auth/         # Authentication components
│   │   ├── teams/        # Team management components
│   │   └── ui/           # Base UI components
│   ├── pages/            # Page components
│   ├── stores/           # Zustand stores
│   ├── types/            # TypeScript definitions
│   └── utils/            # Utility functions
└── public/               # Static assets
```