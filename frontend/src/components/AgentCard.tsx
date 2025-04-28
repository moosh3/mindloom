import React from 'react';
import { Agent } from '../types';
import { agentIconMap } from '../utils/data';

interface AgentCardProps {
  agent: Agent;
  onClick?: () => void;
}

const AgentCard: React.FC<AgentCardProps> = ({ agent, onClick }) => {
  const IconComponent = agentIconMap[agent.icon] || agentIconMap.default;
  
  // Generate a pastel color based on the agent category
  const getIconBackgroundColor = (category: string) => {
    const colorMap: Record<string, string> = {
      'popular': 'bg-purple-100',
      'customer-service': 'bg-blue-100',
      'sales': 'bg-green-100',
      'engineering': 'bg-indigo-100',
      'support': 'bg-orange-100',
      'marketing': 'bg-pink-100',
      'it': 'bg-gray-100',
      'hr': 'bg-yellow-100',
      'default': 'bg-gray-100',
    };
    
    return colorMap[category] || colorMap.default;
  };
  
  const getIconColor = (category: string) => {
    const colorMap: Record<string, string> = {
      'popular': 'text-purple-500',
      'customer-service': 'text-blue-500',
      'sales': 'text-green-500',
      'engineering': 'text-indigo-500',
      'support': 'text-orange-500',
      'marketing': 'text-pink-500',
      'it': 'text-gray-500',
      'hr': 'text-yellow-500',
      'default': 'text-gray-500',
    };
    
    return colorMap[category] || colorMap.default;
  };
  
  return (
    <div 
      onClick={onClick}
      className="flex cursor-pointer flex-col justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-all hover:shadow-md hover:border-gray-300"
    >
      <div className="mb-4">
        <div className={`inline-flex h-10 w-10 items-center justify-center rounded-full ${getIconBackgroundColor(agent.category)}`}>
          <IconComponent className={`h-5 w-5 ${getIconColor(agent.category)}`} />
        </div>
        <h3 className="mt-3 text-base font-semibold text-gray-900">{agent.name}</h3>
        <p className="mt-1 text-sm text-gray-500">{agent.description}</p>
      </div>
      
      {agent.isCustom && agent.createdAt && (
        <div className="mt-4 border-t border-gray-100 pt-3">
          <span className="text-xs text-gray-500">
            Created {agent.createdAt.toLocaleDateString()}
          </span>
        </div>
      )}
    </div>
  );
};

export default AgentCard;