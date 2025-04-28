import React, { useState } from 'react';
import { X, Clock, FileText, Plus } from 'lucide-react';
import Button from './ui/Button';
import TextArea from './ui/TextArea';
import { agentIconMap } from '../utils/data';
import ScheduleBuilder from './scheduling/ScheduleBuilder';
import { Schedule, ScheduleValidationError, ContentBucket } from '../types';

interface Tool {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

interface AgentSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent: {
    name: string;
    description: string;
    icon: string;
    instructions: string;
    schedule?: Schedule;
    contentBuckets?: ContentBucket[];
  };
  onSave: (settings: {
    name: string;
    description: string;
    icon: string;
    instructions: string;
    tools: Tool[];
    schedule?: Schedule;
    contentBuckets: ContentBucket[];
  }) => void;
  availableContentBuckets: ContentBucket[];
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

const AgentSettingsModal: React.FC<AgentSettingsModalProps> = ({
  isOpen,
  onClose,
  agent,
  onSave,
  availableContentBuckets,
}) => {
  const [name, setName] = useState(agent.name);
  const [description, setDescription] = useState(agent.description);
  const [selectedIcon, setSelectedIcon] = useState(agent.icon);
  const [instructions, setInstructions] = useState(agent.instructions);
  const [showIconSelector, setShowIconSelector] = useState(false);
  const [tools, setTools] = useState<Tool[]>(defaultTools);
  const [schedule, setSchedule] = useState<Schedule>(
    agent.schedule || {
      enabled: false,
      frequency: 'daily',
      interval: 1,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    }
  );
  const [scheduleErrors, setScheduleErrors] = useState<ScheduleValidationError[]>([]);
  const [selectedBuckets, setSelectedBuckets] = useState<Set<string>>(
    new Set(agent.contentBuckets?.map(bucket => bucket.id) || [])
  );

  if (!isOpen) return null;

  const handleToolToggle = (toolId: string) => {
    setTools(tools.map(tool => 
      tool.id === toolId ? { ...tool, enabled: !tool.enabled } : tool
    ));
  };

  const handleBucketToggle = (bucketId: string) => {
    const newSelected = new Set(selectedBuckets);
    if (newSelected.has(bucketId)) {
      newSelected.delete(bucketId);
    } else {
      newSelected.add(bucketId);
    }
    setSelectedBuckets(newSelected);
  };

  const handleSave = () => {
    if (schedule.enabled && scheduleErrors.length > 0) {
      return;
    }
    
    const selectedBucketObjects = availableContentBuckets.filter(
      bucket => selectedBuckets.has(bucket.id)
    );

    onSave({
      name,
      description,
      icon: selectedIcon,
      instructions,
      tools: tools.filter(tool => tool.enabled),
      schedule: schedule.enabled ? schedule : undefined,
      contentBuckets: selectedBucketObjects,
    });
    onClose();
  };

  const IconComponent = agentIconMap[selectedIcon] || agentIconMap.default;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative w-[90vw] max-w-2xl max-h-[90vh] overflow-hidden rounded-xl bg-background shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-xl font-semibold text-text">Agent settings</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-background-secondary"
          >
            <X className="h-5 w-5 text-text-secondary" />
          </button>
        </div>

        <div className="overflow-y-auto p-6">
          <div className="space-y-6">
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
                  className="flex items-center space-x-2 rounded-md border border-border bg-background px-4 py-2 text-sm text-text hover:bg-background-secondary"
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

            <div>
              <label className="mb-1 block text-sm font-medium text-text">
                Instructions
              </label>
              <TextArea
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Give instructions to your agent..."
                className="min-h-[150px]"
              />
            </div>

            <div>
              <h3 className="mb-4 flex items-center space-x-2 text-base font-medium text-text">
                <FileText className="h-5 w-5" />
                <span>Content Buckets</span>
              </h3>
              <div className="space-y-4">
                {availableContentBuckets.map((bucket) => (
                  <div
                    key={bucket.id}
                    className="flex items-center justify-between rounded-lg border border-border bg-background-secondary p-4"
                  >
                    <div>
                      <h4 className="text-sm font-medium text-text">{bucket.name}</h4>
                      <p className="text-sm text-text-secondary">{bucket.description}</p>
                      <p className="mt-1 text-xs text-text-tertiary">
                        {bucket.files.length} files
                      </p>
                    </div>
                    <label className="relative inline-flex cursor-pointer items-center">
                      <input
                        type="checkbox"
                        checked={selectedBuckets.has(bucket.id)}
                        onChange={() => handleBucketToggle(bucket.id)}
                        className="peer sr-only"
                      />
                      <div className="h-6 w-11 rounded-full bg-background-tertiary after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-border after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:ring-2 peer-focus:ring-primary"></div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="mb-4 text-base font-medium text-text">Tools</h3>
              <div className="space-y-4">
                {tools.map((tool) => (
                  <div
                    key={tool.id}
                    className="flex items-center justify-between rounded-lg border border-border bg-background-secondary p-4"
                  >
                    <div>
                      <h4 className="text-sm font-medium text-text">{tool.name}</h4>
                      <p className="text-sm text-text-secondary">{tool.description}</p>
                    </div>
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
                ))}
              </div>
            </div>

            <div>
              <h3 className="mb-4 flex items-center space-x-2 text-base font-medium text-text">
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

          <div className="mt-6 flex justify-end space-x-3">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={
                !name.trim() ||
                !description.trim() ||
                !instructions.trim() ||
                (schedule.enabled && scheduleErrors.length > 0)
              }
            >
              Save changes
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentSettingsModal;