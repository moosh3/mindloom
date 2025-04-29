import React, { useState, useMemo } from 'react';
import { Search, Plus } from 'lucide-react';
import Header from '../components/Header';
import Tabs from '../components/ui/Tabs';
import AgentCatalog from '../components/AgentCatalog';
import CreateAgent from './CreateAgent';
import { Agent } from '../types';
import { agentTemplates, tabOptions, userAgents } from '../utils/data';
import Button from '../components/ui/Button';

interface DashboardProps {
  onStartChat?: (agent: Agent) => void;
  onAgentSelect?: (agent: Agent) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onStartChat, onAgentSelect }) => {
  const [activeTab, setActiveTab] = useState('all');
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<Agent | null>(null);
  
  const filteredAgents = useMemo(() => {
    const query = searchQuery.toLowerCase();
    if (!query) return null;

    return [...agentTemplates, ...userAgents].filter(agent =>
      agent.name.toLowerCase().includes(query) ||
      agent.description.toLowerCase().includes(query)
    );
  }, [searchQuery]);
  
  const popularAgents = agentTemplates.filter(
    agent => agent.category === 'popular'
  ).slice(0, 4);
  
  const recommendedAgents = userAgents
    .filter(agent => ['sales', 'engineering', 'support'].includes(agent.category))
    .sort((a, b) => (b.createdAt?.getTime() || 0) - (a.createdAt?.getTime() || 0))
    .slice(0, 4);

  const remainingAgents = useMemo(() => {
    const popularIds = new Set(popularAgents.map(a => a.id));
    const recommendedIds = new Set(recommendedAgents.map(a => a.id));
    
    // Convert remaining templates to non-template agents
    const convertedTemplates = agentTemplates
      .filter(agent => !popularIds.has(agent.id))
      .map(template => ({
        ...template,
        isCustom: true,
        createdAt: new Date()
      }));
    
    const remainingUserAgents = userAgents.filter(
      agent => !recommendedIds.has(agent.id)
    );
    
    return [...convertedTemplates, ...remainingUserAgents];
  }, [popularAgents, recommendedAgents]);
  
  const filteredUserAgents = userAgents.filter(agent => 
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.description.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const handleCreateAgent = () => {
    setSelectedTemplate(null);
    setIsCreating(true);
  };
  
  const handleTemplateSelect = (template: Agent) => {
    setSelectedTemplate(template);
    setIsCreating(true);
  };
  
  const handleGenerateAgent = (settings: any) => {
    const newAgent = {
      id: 'new-' + Date.now(),
      name: settings.name,
      description: settings.description,
      icon: settings.icon,
      category: selectedTemplate?.category || 'popular',
      isCustom: true,
      createdAt: new Date(),
      schedule: settings.schedule,
      variables: settings.variables,
      instructions: settings.instructions,
    };
    
    if (onStartChat) {
      onStartChat(newAgent);
    }
    setIsCreating(false);
  };

  const handleAgentClick = (agent: Agent, isTemplate: boolean = false) => {
    if (isTemplate) {
      handleTemplateSelect(agent);
    } else if (onAgentSelect) {
      onAgentSelect(agent);
    }
  };
  
  if (isCreating) {
    return (
      <CreateAgent
        onBack={() => {
          setIsCreating(false);
          setSelectedTemplate(null);
        }}
        onGenerate={handleGenerateAgent}
        template={selectedTemplate}
      />
    );
  }
  
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="text-xl font-semibold text-text">Agents</h1>
        <Button 
          variant="primary" 
          icon={<Plus className="h-4 w-4" />}
          onClick={handleCreateAgent}
        >
          Create agent
        </Button>
      </div>
      
      <div className="flex flex-col flex-1 px-6 py-6">
        <div className="mb-6">
          <Tabs 
            tabs={tabOptions} 
            activeTab={activeTab} 
            onTabChange={setActiveTab} 
          />
        </div>
        
        <div className="mb-6">
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <Search className="h-5 w-5 text-text-tertiary" />
            </div>
            <input
              type="text"
              placeholder="Search agents..."
              className="w-full rounded-md border border-border bg-background py-2 pl-10 pr-4 text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        
        {searchQuery ? (
          filteredAgents && (
            <AgentCatalog
              title="Search Results"
              agents={filteredAgents}
              onAgentSelect={(agent) => handleAgentClick(agent, agentTemplates.some(t => t.id === agent.id))}
              description={`Found ${filteredAgents.length} agents matching "${searchQuery}"`}
            />
          )
        ) : activeTab === 'all' ? (
          <>
            <AgentCatalog
              title="Popular templates"
              agents={popularAgents}
              onAgentSelect={(agent) => handleAgentClick(agent, true)}
            />
            
            <AgentCatalog
              title="Recommended for you"
              agents={recommendedAgents}
              onAgentSelect={(agent) => handleAgentClick(agent, false)}
              description="Your most relevant and recently created agents"
            />

            <AgentCatalog
              title="All agents"
              agents={remainingAgents}
              onAgentSelect={(agent) => handleAgentClick(agent, false)}
              description="Browse all available agents"
            />
          </>
        ) : activeTab === 'created' ? (
          <AgentCatalog
            title="Your agents"
            agents={filteredUserAgents}
            onAgentSelect={(agent) => handleAgentClick(agent, false)}
          />
        ) : activeTab === 'scheduled' ? (
          <div className="flex h-40 items-center justify-center rounded-lg border-2 border-dashed border-border bg-background-secondary">
            <p className="text-center text-text-secondary">No scheduled agents yet</p>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default Dashboard;