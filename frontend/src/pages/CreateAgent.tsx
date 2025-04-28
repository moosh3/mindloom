import React, { useState, useEffect } from 'react';
import { ArrowLeft, Bot, Clock, Plus, Trash2 } from 'lucide-react';
import Button from '../components/ui/Button';
import TextArea from '../components/ui/TextArea';
import { agentIconMap } from '../utils/data';
import ScheduleBuilder from '../components/scheduling/ScheduleBuilder';
import { Schedule, ScheduleValidationError, AgentVariable, Agent } from '../types';

interface Tool {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

const defaultTools: Tool[] = [
  {
    id: 'salesforce',
    name: 'Salesforce',
    description: 'Search for calls in Gong for integrations',
    enabled: true,
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Search for messages in Slack for company',
    enabled: true,
  },
  {
    id: 'jira',
    name: 'Jira',
    description: 'Search the Jira release tracking product roadmap',
    enabled: true,
  },
  {
    id: 'gong',
    name: 'Gong',
    description: 'Track customer feature history',
    enabled: true,
  },
];

const defaultSchedule: Schedule = {
  enabled: false,
  frequency: 'daily',
  interval: 1,
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
};

interface CreateAgentProps {
  onBack: () => void;
  onGenerate: (settings: {
    name: string;
    description: string;
    icon: string;
    instructions: string;
    tools: Tool[];
    schedule?: Schedule;
    variables: AgentVariable[];
  }) => void;
  template?: Agent | null;
}

const CreateAgent: React.FC<CreateAgentProps> = ({ onBack, onGenerate, template }) => {
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [instructions, setInstructions] = useState(template?.instructions || '');
  const [selectedIcon, setSelectedIcon] = useState(template?.icon || 'default');
  const [showIconSelector, setShowIconSelector] = useState(false);
  const [tools, setTools] = useState<Tool[]>(defaultTools);
  const [schedule, setSchedule] = useState<Schedule>(template?.schedule || defaultSchedule);
  const [scheduleErrors, setScheduleErrors] = useState<ScheduleValidationError[]>([]);
  const [variables, setVariables] = useState<AgentVariable[]>(template?.variables || []);

  useEffect(() => {
    if (template) {
      setName(template.name);
      setDescription(template.description);
      setInstructions(template.instructions || '');
      setSelectedIcon(template.icon);
      if (template.schedule) {
        setSchedule(template.schedule);
      }
      if (template.variables) {
        setVariables(template.variables);
      }
    }
  }, [template]);

  const handleToolToggle = (toolId: string) => {
    setTools(tools.map(tool => 
      tool.id === toolId ? { ...tool, enabled: !tool.enabled } : tool
    ));
  };
  
  const handleAddVariable = () => {
    setVariables([...variables, { name: '', description: '' }]);
  };

  const handleRemoveVariable = (index: number) => {
    setVariables(variables.filter((_, i) => i !== index));
  };

  const handleVariableChange = (index: number, field: 'name' | 'description', value: string) => {
    setVariables(variables.map((variable, i) => 
      i === index ? { ...variable, [field]: value } : variable
    ));
  };
  
  const handleGenerate = () => {
    if (schedule.enabled && scheduleErrors.length > 0) {
      return;
    }
    
    onGenerate({
      name,
      description,
      icon: selectedIcon,
      instructions,
      tools: tools.filter(tool => tool.enabled),
      schedule: schedule.enabled ? schedule : undefined,
      variables,
    });
  };

  const IconComponent = agentIconMap[selectedIcon] || agentIconMap.default;
  
  return (
    <div className="flex h-full flex-col bg-background">
      <div className="flex items-center border-b border-border px-6 py-4">
        <button
          onClick={onBack}
          className="mr-4 rounded-md p-1 hover:bg-background-secondary"
        >
          <ArrowLeft className="h-5 w-5 text-text-secondary" />
        </button>
        <h2 className="text-xl font-semibold text-text">
          {template ? `Customize ${template.name}` : 'Create from scratch'}
        </h2>
      </div>
      
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-3xl space-y-8">
            <div className="space-y-6">
              <div>
                <h3 className="mb-4 text-lg font-medium text-text">Basic Information</h3>
                <div className="space-y-4 rounded-lg border border-border bg-background-secondary p-6">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-text">
                      Name
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="Enter agent name"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-text">
                      Description
                    </label>
                    <input
                      type="text"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      placeholder="Enter agent description"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-text">
                      Icon
                    </label>
                    <div className="relative">
                      <button
                        onClick={() => setShowIconSelector(!showIconSelector)}
                        className="flex items-center space-x-2 rounded-md border border-border bg-background px-4 py-2 text-sm text-text hover:border-primary"
                      >
                        <IconComponent className="h-5 w-5 text-primary" />
                        <span>Change Icon</span>
                      </button>

                      {showIconSelector && (
                        <div className="absolute left-0 right-0 top-full z-10 mt-1 grid max-h-48 grid-cols-6 gap-2 overflow-y-auto rounded-md border border-border bg-background p-2 shadow-lg">
                          {Object.entries(agentIconMap).map(([key, Icon]) => (
                            <button
                              key={key}
                              onClick={() => {
                                setSelectedIcon(key);
                                setShowIconSelector(false);
                              }}
                              className={`flex items-center justify-center rounded-md p-2 hover:bg-background-secondary ${
                                selectedIcon === key ? 'bg-background-tertiary' : ''
                              }`}
                            >
                              <Icon className="h-5 w-5 text-primary" />
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="mb-4 text-lg font-medium text-text">Variables</h3>
                <div className="rounded-lg border border-border bg-background-secondary p-6">
                  <div className="space-y-4">
                    {variables.map((variable, index) => (
                      <div key={index} className="relative rounded-lg border border-border bg-background p-4">
                        <button
                          onClick={() => handleRemoveVariable(index)}
                          className="absolute right-2 top-2 rounded-md p-1 text-text-secondary hover:bg-background-secondary hover:text-primary"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                        <div className="space-y-3">
                          <div>
                            <label className="mb-1 block text-sm font-medium text-text">
                              Variable Name
                            </label>
                            <input
                              type="text"
                              value={variable.name}
                              onChange={(e) => handleVariableChange(index, 'name', e.target.value)}
                              className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                              placeholder="e.g., company_name"
                            />
                          </div>
                          <div>
                            <label className="mb-1 block text-sm font-medium text-text">
                              Description
                            </label>
                            <input
                              type="text"
                              value={variable.description}
                              onChange={(e) => handleVariableChange(index, 'description', e.target.value)}
                              className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                              placeholder="e.g., Name of the company to analyze"
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                    <Button
                      variant="outline"
                      onClick={handleAddVariable}
                      icon={<Plus className="h-4 w-4" />}
                      className="w-full"
                    >
                      Add Variable
                    </Button>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="mb-4 text-lg font-medium text-text">Instructions</h3>
                <div className="rounded-lg border border-border bg-background-secondary p-6">
                  <TextArea
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    placeholder="Give instructions to your agent with as many details as possible..."
                    className="min-h-[200px]"
                  />
                </div>
              </div>

              <div>
                <h3 className="mb-4 text-lg font-medium text-text">Tools</h3>
                <div className="grid grid-cols-2 gap-4">
                  {tools.map((tool) => (
                    <div
                      key={tool.id}
                      className="flex items-center justify-between rounded-lg border border-border bg-background-secondary p-4"
                    >
                      <div className="min-w-0 flex-1 pr-4">
                        <h4 className="text-sm font-medium text-text">{tool.name}</h4>
                        <p className="text-sm text-text-secondary truncate">{tool.description}</p>
                      </div>
                      <div className="flex-shrink-0">
                        <label className="relative inline-flex cursor-pointer items-center">
                          <input
                            type="checkbox"
                            checked={tool.enabled}
                            onChange={() => handleToolToggle(tool.id)}
                            className="peer sr-only"
                          />
                          <div className="h-6 w-11 rounded-full bg-background-tertiary after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-border after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:ring-2 peer-focus:ring-primary"></div>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="mb-4 flex items-center space-x-2 text-lg font-medium text-text">
                  <Clock className="h-5 w-5" />
                  <span>Schedule</span>
                </h3>
                <div className="rounded-lg border border-border bg-background-secondary p-6">
                  <ScheduleBuilder
                    value={schedule}
                    onChange={setSchedule}
                    onValidationError={setScheduleErrors}
                  />
                </div>
              </div>
            </div>

            <div className="sticky bottom-0 flex justify-end space-x-3 border-t border-border bg-background py-4">
              <Button variant="outline" onClick={onBack}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleGenerate}
                disabled={
                  !name.trim() ||
                  !description.trim() ||
                  !instructions.trim() ||
                  (schedule.enabled && scheduleErrors.length > 0) ||
                  variables.some(v => !v.name.trim() || !v.description.trim())
                }
              >
                Generate
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateAgent;