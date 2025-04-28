import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { Agent } from '../types';
import { agentTemplates, userAgents } from '../utils/data';
import { agentIconMap } from '../utils/data';

interface AgentSelectProps {
  onSelect: (agent: Agent) => void;
  onClose: () => void;
}

const AgentSelect: React.FC<AgentSelectProps> = ({ onSelect, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isOpen, setIsOpen] = useState(true);
  
  const allAgents = [...agentTemplates, ...userAgents];
  const filteredAgents = allAgents.filter(agent =>
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.description.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const handleSelect = (agent: Agent) => {
    onSelect(agent);
    setIsOpen(false);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="rounded-lg border border-border bg-background p-4 shadow-lg">
      <div className="relative mb-3">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <Search className="h-4 w-4 text-text-secondary" />
        </div>
        <input
          type="text"
          placeholder="Search agents..."
          className="w-full rounded-md border border-border bg-background py-2 pl-10 pr-4 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
      
      <div className="max-h-64 overflow-y-auto">
        {filteredAgents.map((agent) => {
          const IconComponent = agentIconMap[agent.icon] || agentIconMap.default;
          return (
            <button
              key={agent.id}
              onClick={() => handleSelect(agent)}
              className="flex w-full items-center space-x-3 rounded-md p-2 text-left hover:bg-background-secondary"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-background-secondary">
                <IconComponent className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-medium text-text truncate">{agent.name}</p>
                <p className="text-xs text-text-secondary truncate">{agent.description}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default AgentSelect;