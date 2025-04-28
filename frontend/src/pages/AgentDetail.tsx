import React, { useState } from 'react';
import { ArrowLeft, Settings, Play, Bot } from 'lucide-react';
import Button from '../components/ui/Button';
import AgentSettingsModal from '../components/AgentSettingsModal';
import { Agent } from '../types';

interface AgentDetailProps {
  onBack: () => void;
  agent: Agent;
}

const AgentDetail: React.FC<AgentDetailProps> = ({ onBack, agent }) => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [variableValues, setVariableValues] = useState<Record<string, string>>(
    agent.variables?.reduce((acc, v) => ({ ...acc, [v.name]: '' }), {}) || {}
  );
  
  const handleVariableChange = (name: string, value: string) => {
    setVariableValues(prev => ({ ...prev, [name]: value }));
  };
  
  const handleRun = () => {
    // Here you would handle running the agent with the variable values
    console.log('Running agent with variables:', variableValues);
  };

  const canRun = !agent.variables || 
    agent.variables.every(v => variableValues[v.name]?.trim());
  
  return (
    <div className="flex h-full flex-col bg-background">
      <div className="flex items-center justify-between border-b border-border bg-background px-6 py-4">
        <div className="flex items-center">
          <button
            onClick={onBack}
            className="mr-4 rounded-md p-1 hover:bg-background-secondary"
          >
            <ArrowLeft className="h-5 w-5 text-text-secondary" />
          </button>
          <div className="flex items-center">
            <div className="mr-3 rounded-lg bg-background-secondary p-2">
              <Bot className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-text">{agent.name}</h1>
              <p className="text-sm text-text-secondary">{agent.description}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Button 
            variant="outline" 
            icon={<Settings className="h-4 w-4" />}
            onClick={() => setIsSettingsOpen(true)}
          >
            Settings
          </Button>
          <Button 
            variant="primary" 
            icon={<Play className="h-4 w-4" />}
            onClick={handleRun}
            disabled={!canRun}
          >
            Run
          </Button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl">
          {agent.variables && agent.variables.length > 0 && (
            <div className="mb-6 rounded-lg bg-background-secondary p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-medium text-text">Variables</h2>
              <div className="space-y-4">
                {agent.variables.map((variable) => (
                  <div key={variable.name}>
                    <label className="mb-1 block text-sm font-medium text-text">
                      {variable.name}
                    </label>
                    <p className="mb-2 text-sm text-text-secondary">{variable.description}</p>
                    <input
                      type="text"
                      value={variableValues[variable.name] || ''}
                      onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-4 py-2 text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder={`Enter ${variable.name}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="rounded-lg bg-background-secondary p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-medium text-text">Instructions</h2>
            <div className="rounded-md bg-background p-4">
              <p className="text-sm text-text-secondary">{agent.instructions}</p>
            </div>
          </div>
        </div>
      </div>

      <AgentSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        agent={{
          name: agent.name,
          description: agent.description,
          icon: agent.icon || 'default',
          instructions: agent.instructions || '',
          schedule: agent.schedule,
        }}
        onSave={(settings) => {
          // Here you would handle saving the updated settings
          setIsSettingsOpen(false);
        }}
      />
    </div>
  );
};

export default AgentDetail;