import React, { useState } from 'react';
import { ArrowLeft, X, Bot, Clock } from 'lucide-react';
import Button from './ui/Button';
import TextArea from './ui/TextArea';
import { agentIconMap } from '../utils/data';
import ScheduleBuilder from './scheduling/ScheduleBuilder';
import { Schedule, ScheduleValidationError } from '../types';

interface CreateFromScratchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (settings: {
    name: string;
    description: string;
    icon: string;
    instructions: string;
    tools: Tool[];
    schedule?: Schedule;
  }) => void;
}

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

const CreateFromScratchModal: React.FC<CreateFromScratchModalProps> = ({
  isOpen,
  onClose,
  onGenerate,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [instructions, setInstructions] = useState('');
  const [selectedIcon, setSelectedIcon] = useState('default');
  const [showIconSelector, setShowIconSelector] = useState(false);
  const [tools, setTools] = useState<Tool[]>(defaultTools);
  const [schedule, setSchedule] = useState<Schedule>(defaultSchedule);
  const [scheduleErrors, setScheduleErrors] = useState<ScheduleValidationError[]>([]);
  
  if (!isOpen) return null;

  const handleToolToggle = (toolId: string) => {
    setTools(tools.map(tool => 
      tool.id === toolId ? { ...tool, enabled: !tool.enabled } : tool
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
    });
  };

  const IconComponent = agentIconMap[selectedIcon] || agentIconMap.default;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative w-[90vw] max-w-2xl max-h-[90vh] overflow-hidden rounded-xl bg-drw-dark shadow-xl">
        <div className="flex items-center border-b border-drw-dark-lighter px-6 py-4">
          <button
            onClick={onClose}
            className="mr-4 rounded-md p-1 hover:bg-drw-dark-light"
          >
            <ArrowLeft className="h-5 w-5 text-gray-400" />
          </button>
          <h2 className="text-xl font-semibold text-drw-gold">Create from scratch</h2>
          <button
            onClick={onClose}
            className="ml-auto rounded-md p-1 hover:bg-drw-dark-light"
          >
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>
        
        <div className="overflow-y-auto p-6">
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-200">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-drw-dark-lighter bg-drw-dark-light px-4 py-2 text-sm text-gray-200 placeholder-gray-400 focus:border-drw-gold focus:outline-none focus:ring-1 focus:ring-drw-gold"
              placeholder="Enter agent name"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-200">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-md border border-drw-dark-lighter bg-drw-dark-light px-4 py-2 text-sm text-gray-200 placeholder-gray-400 focus:border-drw-gold focus:outline-none focus:ring-1 focus:ring-drw-gold"
              placeholder="Enter agent description"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-200">
              Icon
            </label>
            <div className="relative">
              <button
                onClick={() => setShowIconSelector(!showIconSelector)}
                className="flex items-center space-x-2 rounded-md border border-drw-dark-lighter bg-drw-dark-light px-4 py-2 text-sm text-gray-200 hover:border-drw-gold"
              >
                <IconComponent className="h-5 w-5 text-drw-gold" />
                <span>Change Icon</span>
              </button>

              {showIconSelector && (
                <div className="absolute left-0 right-0 top-full z-10 mt-1 grid max-h-48 grid-cols-4 gap-2 overflow-y-auto rounded-md border border-drw-dark-lighter bg-drw-dark p-2 shadow-lg">
                  {Object.entries(agentIconMap).map(([key, Icon]) => (
                    <button
                      key={key}
                      onClick={() => {
                        setSelectedIcon(key);
                        setShowIconSelector(false);
                      }}
                      className={`flex items-center justify-center rounded-md p-2 hover:bg-drw-dark-light ${
                        selectedIcon === key ? 'bg-drw-dark-lighter' : ''
                      }`}
                    >
                      <Icon className="h-5 w-5 text-drw-gold" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-200">
              Instructions
            </label>
            <TextArea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Give instructions to your agent with as many details as possible..."
              className="min-h-[100px]"
            />
          </div>

          <div className="mb-4">
            <h3 className="mb-2 text-sm font-medium text-gray-200">Tools</h3>
            <div className="space-y-2">
              {tools.map((tool) => (
                <div
                  key={tool.id}
                  className="flex items-center justify-between rounded-lg border border-drw-dark-lighter bg-drw-dark-light p-3"
                >
                  <div className="min-w-0 flex-1 pr-4">
                    <h4 className="text-sm font-medium text-gray-200">{tool.name}</h4>
                    <p className="text-xs text-gray-400 truncate">{tool.description}</p>
                  </div>
                  <div className="flex-shrink-0">
                    <label className="relative inline-flex cursor-pointer items-center">
                      <input
                        type="checkbox"
                        checked={tool.enabled}
                        onChange={() => handleToolToggle(tool.id)}
                        className="peer sr-only"
                      />
                      <div className="h-5 w-9 rounded-full bg-drw-dark-lighter after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-drw-gold peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:ring-2 peer-focus:ring-drw-gold"></div>
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <h3 className="mb-2 flex items-center space-x-2 text-sm font-medium text-gray-200">
              <Clock className="h-4 w-4" />
              <span>Schedule</span>
            </h3>
            <ScheduleBuilder
              value={schedule}
              onChange={setSchedule}
              onValidationError={setScheduleErrors}
            />
          </div>
          
          <div className="mt-6 flex justify-end space-x-3">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleGenerate}
              disabled={
                !name.trim() ||
                !description.trim() ||
                !instructions.trim() ||
                (schedule.enabled && scheduleErrors.length > 0)
              }
            >
              Generate
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateFromScratchModal;