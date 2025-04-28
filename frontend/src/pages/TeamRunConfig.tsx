import React, { useState } from 'react';
import { ArrowLeft, Play, Clock, Users } from 'lucide-react';
import Button from '../components/ui/Button';
import { Team, AgentVariable } from '../types';

interface TeamRunConfigProps {
  team: Team;
  onBack: () => void;
  onRun: (config: {
    teamVariables: Record<string, string>;
    agentVariables: Record<string, Record<string, string>>;
    streamLogs: boolean;
    scheduledTime?: Date;
  }) => void;
}

const TeamRunConfig: React.FC<TeamRunConfigProps> = ({ team, onBack, onRun }) => {
  const [teamVariables, setTeamVariables] = useState<Record<string, string>>({});
  const [agentVariables, setAgentVariables] = useState<Record<string, Record<string, string>>>({});
  const [streamLogs, setStreamLogs] = useState(true);
  const [executionType, setExecutionType] = useState<'immediate' | 'scheduled'>('immediate');
  const [scheduledTime, setScheduledTime] = useState<string>('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    // Validate team variables
    if (team.variables) {
      team.variables.forEach(variable => {
        if (!teamVariables[variable.name]?.trim()) {
          newErrors[`team-${variable.name}`] = 'This field is required';
        }
      });
    }

    // Validate agent variables
    team.agents.forEach(agent => {
      if (agent.variables) {
        agent.variables.forEach(variable => {
          if (!agentVariables[agent.id]?.[variable.name]?.trim()) {
            newErrors[`${agent.id}-${variable.name}`] = 'This field is required';
          }
        });
      }
    });

    // Validate scheduled time
    if (executionType === 'scheduled') {
      if (!scheduledTime) {
        newErrors.scheduledTime = 'Scheduled time is required';
      } else {
        const selectedTime = new Date(scheduledTime);
        if (selectedTime <= new Date()) {
          newErrors.scheduledTime = 'Scheduled time must be in the future';
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRun = () => {
    if (!validateForm()) return;

    onRun({
      teamVariables,
      agentVariables,
      streamLogs,
      ...(executionType === 'scheduled' ? { scheduledTime: new Date(scheduledTime) } : {}),
    });
  };

  const handleTeamVariableChange = (name: string, value: string) => {
    setTeamVariables(prev => ({
      ...prev,
      [name]: value,
    }));
    
    const errorKey = `team-${name}`;
    if (errors[errorKey]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[errorKey];
        return newErrors;
      });
    }
  };

  const handleAgentVariableChange = (agentId: string, name: string, value: string) => {
    setAgentVariables(prev => ({
      ...prev,
      [agentId]: {
        ...(prev[agentId] || {}),
        [name]: value,
      },
    }));
    
    const errorKey = `${agentId}-${name}`;
    if (errors[errorKey]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[errorKey];
        return newErrors;
      });
    }
  };

  // Get minimum datetime for scheduler (current time + 5 minutes)
  const getMinDateTime = () => {
    const date = new Date();
    date.setMinutes(date.getMinutes() + 5);
    return date.toISOString().slice(0, 16);
  };

  return (
    <div className="flex h-full flex-col bg-background">
      <div className="flex items-center border-b border-border px-6 py-4">
        <button
          onClick={onBack}
          className="mr-4 rounded-md p-1 hover:bg-background-secondary"
        >
          <ArrowLeft className="h-5 w-5 text-text-secondary" />
        </button>
        <div>
          <h1 className="text-xl font-semibold text-text">Team Run Configuration</h1>
          <p className="text-sm text-text-secondary">{team.name}</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-2xl space-y-8">
          {team.variables && team.variables.length > 0 && (
            <div>
              <h2 className="mb-4 text-lg font-medium text-text">Team Variables</h2>
              <div className="space-y-4 rounded-lg border border-border bg-background-secondary p-6">
                {team.variables.map((variable: AgentVariable) => (
                  <div key={variable.name}>
                    <label className="mb-1 block text-sm font-medium text-text">
                      {variable.name}
                    </label>
                    <p className="mb-2 text-sm text-text-secondary">
                      {variable.description}
                    </p>
                    <input
                      type="text"
                      value={teamVariables[variable.name] || ''}
                      onChange={(e) => handleTeamVariableChange(variable.name, e.target.value)}
                      className={`w-full rounded-md border ${
                        errors[`team-${variable.name}`] ? 'border-red-500' : 'border-border'
                      } bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary`}
                      placeholder={`Enter ${variable.name}`}
                    />
                    {errors[`team-${variable.name}`] && (
                      <p className="mt-1 text-sm text-red-500">{errors[`team-${variable.name}`]}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {team.agents.map(agent => (
            agent.variables && agent.variables.length > 0 && (
              <div key={agent.id}>
                <h2 className="mb-4 text-lg font-medium text-text">{agent.name} Variables</h2>
                <div className="space-y-4 rounded-lg border border-border bg-background-secondary p-6">
                  {agent.variables.map((variable: AgentVariable) => (
                    <div key={variable.name}>
                      <label className="mb-1 block text-sm font-medium text-text">
                        {variable.name}
                      </label>
                      <p className="mb-2 text-sm text-text-secondary">
                        {variable.description}
                      </p>
                      <input
                        type="text"
                        value={agentVariables[agent.id]?.[variable.name] || ''}
                        onChange={(e) => handleAgentVariableChange(agent.id, variable.name, e.target.value)}
                        className={`w-full rounded-md border ${
                          errors[`${agent.id}-${variable.name}`] ? 'border-red-500' : 'border-border'
                        } bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary`}
                        placeholder={`Enter ${variable.name}`}
                      />
                      {errors[`${agent.id}-${variable.name}`] && (
                        <p className="mt-1 text-sm text-red-500">{errors[`${agent.id}-${variable.name}`]}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )
          ))}

          <div>
            <h2 className="mb-4 text-lg font-medium text-text">Execution Settings</h2>
            <div className="space-y-6 rounded-lg border border-border bg-background-secondary p-6">
              <div>
                <label className="mb-4 flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={streamLogs}
                    onChange={(e) => setStreamLogs(e.target.checked)}
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="text-sm font-medium text-text">Stream Logs</span>
                </label>
                <p className="text-sm text-text-secondary">
                  View logs in real-time as the team executes
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-text">
                    Execution Timing
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center space-x-2">
                      <input
                        type="radio"
                        value="immediate"
                        checked={executionType === 'immediate'}
                        onChange={(e) => setExecutionType(e.target.value as 'immediate' | 'scheduled')}
                        className="h-4 w-4 border-border text-primary focus:ring-primary"
                      />
                      <span className="text-sm text-text">Run immediately</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input
                        type="radio"
                        value="scheduled"
                        checked={executionType === 'scheduled'}
                        onChange={(e) => setExecutionType(e.target.value as 'immediate' | 'scheduled')}
                        className="h-4 w-4 border-border text-primary focus:ring-primary"
                      />
                      <span className="text-sm text-text">Schedule for later</span>
                    </label>
                  </div>
                </div>

                {executionType === 'scheduled' && (
                  <div>
                    <label className="mb-1 block text-sm font-medium text-text">
                      Scheduled Time
                    </label>
                    <input
                      type="datetime-local"
                      value={scheduledTime}
                      onChange={(e) => setScheduledTime(e.target.value)}
                      min={getMinDateTime()}
                      className={`w-full rounded-md border ${
                        errors.scheduledTime ? 'border-red-500' : 'border-border'
                      } bg-background px-4 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary`}
                    />
                    {errors.scheduledTime && (
                      <p className="mt-1 text-sm text-red-500">{errors.scheduledTime}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-border bg-background p-6">
        <div className="mx-auto max-w-2xl">
          <Button
            variant="primary"
            onClick={handleRun}
            icon={executionType === 'immediate' ? <Play className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
            className="w-full"
          >
            {executionType === 'immediate' ? 'Run Team' : 'Schedule Run'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TeamRunConfig;