import React, { useState } from 'react';
import { X, Search } from 'lucide-react';
import Button from './ui/Button';
import { Agent } from '../types';
import { agentTemplates, agentIconMap } from '../utils/data';

interface ConnectAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (agents: Agent[]) => void;
  connectedAgents: string[];
}

const ConnectAgentModal: React.FC<ConnectAgentModalProps> = ({
  isOpen,
  onClose,
  onConnect,
  connectedAgents,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<Set<string>>(
    new Set(connectedAgents)
  );

  if (!isOpen) return null;

  const filteredAgents = agentTemplates.filter(
    (agent) =>
      (agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleToggleAgent = (agentId: string) => {
    const newSelected = new Set(selectedAgents);
    if (newSelected.has(agentId)) {
      newSelected.delete(agentId);
    } else {
      newSelected.add(agentId);
    }
    setSelectedAgents(newSelected);
  };

  const handleSave = () => {
    const selectedAgentObjects = agentTemplates.filter((agent) =>
      selectedAgents.has(agent.id)
    );
    onConnect(selectedAgentObjects);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-[90vw] max-w-2xl rounded-xl bg-drw-dark shadow-xl">
        <div className="flex items-center justify-between border-b border-drw-dark-lighter px-6 py-4">
          <h2 className="text-xl font-semibold text-drw-gold">Connect agents</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-drw-dark-light"
          >
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        <div className="p-6">
          <div className="mb-6">
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search agents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border border-drw-dark-lighter bg-drw-dark-light py-2 pl-10 pr-4 text-sm text-gray-200 placeholder-gray-400 focus:border-drw-gold focus:outline-none focus:ring-1 focus:ring-drw-gold"
              />
            </div>
          </div>

          <div className="max-h-[400px] overflow-y-auto">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {filteredAgents.map((agent) => {
                const IconComponent = agentIconMap[agent.icon] || agentIconMap.default;
                const isSelected = selectedAgents.has(agent.id);

                return (
                  <button
                    key={agent.id}
                    onClick={() => handleToggleAgent(agent.id)}
                    className={`flex items-start space-x-3 rounded-lg border p-4 text-left transition-colors ${
                      isSelected
                        ? 'border-drw-gold bg-drw-dark-lighter'
                        : 'border-drw-dark-lighter bg-drw-dark-light hover:border-drw-gold-light'
                    }`}
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-drw-dark">
                      <IconComponent className="h-4 w-4 text-drw-gold" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-200">
                        {agent.name}
                      </h3>
                      <p className="mt-1 text-sm text-gray-400">
                        {agent.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={selectedAgents.size === 0}
            >
              Connect agents
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectAgentModal;