import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Chat from './components/Chat';
import Content from './pages/Content';
import Runs from './pages/Runs';
import RunConfig from './pages/RunConfig';
import RunOutput from './pages/RunOutput';
import Teams from './pages/Teams';
import { Agent } from './types';

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentChat, setCurrentChat] = useState<Agent | null>(null);
  const [currentView, setCurrentView] = useState<'dashboard' | 'chat' | 'content' | 'runs' | 'run-config' | 'run-output' | 'teams'>('dashboard');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  
  const handleStartChat = (agent: Agent) => {
    setCurrentChat(agent);
    setCurrentView('chat');
  };
  
  const handleNavigate = (view: 'dashboard' | 'chat' | 'content' | 'runs' | 'teams') => {
    setCurrentView(view);
    if (view === 'chat' && !currentChat) {
      setCurrentChat({
        id: 'default-agent',
        name: 'AI Assistant',
        description: 'Your general-purpose AI assistant',
        icon: 'default',
        category: 'popular'
      });
    }
  };

  const handleAgentSelect = (agent: Agent) => {
    setSelectedAgent(agent);
    setCurrentView('run-config');
  };

  const handleRunAgent = (config: any) => {
    setCurrentView('run-output');
  };
  
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar 
        collapsed={sidebarCollapsed} 
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onStartChat={handleStartChat}
        onNavigate={handleNavigate}
        currentView={currentView}
      />
      <div className="flex-1 overflow-auto">
        {currentView === 'chat' ? (
          <Chat 
            agent={currentChat!} 
            onBack={() => {
              setCurrentView('dashboard');
              setCurrentChat(null);
            }} 
          />
        ) : currentView === 'content' ? (
          <Content />
        ) : currentView === 'runs' ? (
          <Runs />
        ) : currentView === 'teams' ? (
          <Teams />
        ) : currentView === 'run-config' && selectedAgent ? (
          <RunConfig
            agent={selectedAgent}
            onBack={() => {
              setCurrentView('dashboard');
              setSelectedAgent(null);
            }}
            onRun={handleRunAgent}
          />
        ) : currentView === 'run-output' && selectedAgent ? (
          <RunOutput
            agent={selectedAgent}
            onBack={() => {
              setCurrentView('dashboard');
              setSelectedAgent(null);
            }}
          />
        ) : (
          <Dashboard 
            onStartChat={handleStartChat}
            onAgentSelect={handleAgentSelect}
          />
        )}
      </div>
    </div>
  );
}

export default App;