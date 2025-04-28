import React from 'react';
import { Agent } from '../../types';
import { agentIconMap } from '../../utils/data';
import ScheduleStatus from './ScheduleStatus';

interface ScheduledAgentsProps {
  agents: Agent[];
  onToggleSchedule: (agentId: string) => void;
}

const ScheduledAgents: React.FC<ScheduledAgentsProps> = ({
  agents,
  onToggleSchedule,
}) => {
  const formatLastRun = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date);
  };

  return (
    <div className="space-y-4">
      {agents.map((agent) => {
        const IconComponent = agentIconMap[agent.icon] || agentIconMap.default;
        
        return (
          <div
            key={agent.id}
            className="rounded-lg border border-drw-dark-lighter bg-drw-dark-light p-4"
          >
            <div className="mb-4 flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-drw-dark">
                  <IconComponent className="h-5 w-5 text-drw-gold" />
                </div>
                <div>
                  <h3 className="text-base font-medium text-gray-200">{agent.name}</h3>
                  <p className="text-sm text-gray-400">{agent.description}</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-drw-dark-lighter pt-4">
              {agent.lastRun && (
                <div className="text-sm text-gray-400">
                  Last run: {formatLastRun(agent.lastRun)}
                </div>
              )}
              
              {agent.schedule && (
                <ScheduleStatus
                  schedule={agent.schedule}
                  status={agent.status || 'active'}
                  onToggle={() => onToggleSchedule(agent.id)}
                />
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ScheduledAgents;