import React from 'react';
import { Agent } from '../types';
import AgentCard from './AgentCard';

interface AgentCatalogProps {
  title: string;
  agents: Agent[];
  onAgentSelect: (agent: Agent) => void;
  showSeeAll?: boolean;
  onSeeAllClick?: () => void;
  description?: string;
}

const AgentCatalog: React.FC<AgentCatalogProps> = ({
  title,
  agents,
  onAgentSelect,
  showSeeAll = false,
  onSeeAllClick,
  description,
}) => {
  return (
    <div className="mb-10">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text">{title}</h2>
          {showSeeAll && (
            <button
              onClick={onSeeAllClick}
              className="text-sm font-medium text-primary hover:text-primary-light"
            >
              See all
            </button>
          )}
        </div>
        {description && (
          <p className="mt-1 text-sm text-text-secondary">{description}</p>
        )}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            onClick={() => onAgentSelect(agent)}
          />
        ))}
      </div>
    </div>
  );
};

export default AgentCatalog;