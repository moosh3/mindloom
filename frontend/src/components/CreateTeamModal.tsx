import React, { useState } from 'react';
import { X, Users, Bot, ChevronDown, Plus, Trash2, FileText, Search } from 'lucide-react';
import Button from './ui/Button';
import { Agent, AgentVariable, ContentBucket } from '../types';
import { agentTemplates, userAgents } from '../utils/data';

interface CreateTeamModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (team: {
    name: string;
    description: string;
    type: 'route' | 'coordinate' | 'collaborate';
    agents: Agent[];
    variables: AgentVariable[];
    contentBuckets: ContentBucket[];
  }) => void;
}

const mockContentBuckets: ContentBucket[] = [
  {
    id: '1',
    name: 'Product Documentation',
    description: 'Official product documentation and guides',
    files: [],
    agents: [],
    createdAt: new Date(2024, 1, 15),
  },
  {
    id: '2',
    name: 'Sales Materials',
    description: 'Sales presentations and marketing collateral',
    files: [],
    agents: [],
    createdAt: new Date(2024, 2, 1),
  },
];

const CreateTeamModal: React.FC<CreateTeamModalProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<'route' | 'coordinate' | 'collaborate'>('route');
  const [selectedAgents, setSelectedAgents] = useState<Agent[]>([]);
  const [showAgentSelect, setShowAgentSelect] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [variables, setVariables] = useState<AgentVariable[]>([]);
  const [selectedBuckets, setSelectedBuckets] = useState<Set<string>>(new Set());

  const allAgents = [...agentTemplates, ...userAgents];
  const filteredAgents = allAgents.filter(agent =>
    !selectedAgents.some(a => a.id === agent.id) &&
    (agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (!isOpen) return null;

  const handleAgentSelect = (agent: Agent) => {
    if (selectedAgents.length < 5) {
      setSelectedAgents([...selectedAgents, agent]);
      setSearchQuery('');
    }
  };

  const handleRemoveAgent = (agentId: string) => {
    setSelectedAgents(selectedAgents.filter(agent => agent.id !== agentId));
  };

  const handleAddVariable = () => {
    setVariables([...variables, { name: '', description: '' }]);
  };

  const handleRemoveVariable = (index: number) => {
    setVariables(variables.filter((_, i) => i !== index));
  };

  const handleVariableChange = (index: number, field: keyof AgentVariable, value: string) => {
    setVariables(variables.map((variable, i) => 
      i === index ? { ...variable, [field]: value } : variable
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
    const selectedBucketObjects = mockContentBuckets.filter(
      bucket => selectedBuckets.has(bucket.id)
    );

    onSave({
      name,
      description,
      type,
      agents: selectedAgents,
      variables: variables.filter(v => v.name && v.description),
      contentBuckets: selectedBucketObjects,
    });
    onClose();
  };

  const typeDescriptions = {
    route: 'Agents work independently on assigned tasks',
    coordinate: 'Agents work in sequence, passing results to the next agent',
    collaborate: 'Agents work together, sharing context and knowledge'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-[90vw] max-w-2xl rounded-xl bg-background shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-xl font-semibold text-text">Create new team</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-background-secondary"
          >
            <X className="h-5 w-5 text-text-secondary" />
          </button>
        </div>

        <div className="max-h-[80vh] overflow-y-auto p-6">
          <div className="space-y-6">
            <div>
              <label className="mb-1 block text-sm font-medium text-text">
                Team Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Enter team name"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-text">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Describe the team's purpose"
                rows={3}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-text">
                Team Type
              </label>
              <div className="grid grid-cols-3 gap-4">
                {(['route', 'coordinate', 'collaborate'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setType(t)}
                    className={`flex flex-col items-center rounded-lg border p-4 text-center transition-colors ${
                      type === t
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <span className="mb-2 text-sm font-medium capitalize text-text">
                      {t}
                    </span>
                    <p className="text-xs text-text-secondary">
                      {typeDescriptions[t]}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="text-sm font-medium text-text">
                  Team Variables
                </label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAddVariable}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Add Variable
                </Button>
              </div>
              <div className="space-y-3">
                {variables.map((variable, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-border bg-background-secondary p-4"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <h4 className="text-sm font-medium text-text">
                        Variable {index + 1}
                      </h4>
                      <button
                        onClick={() => handleRemoveVariable(index)}
                        className="rounded-md p-1 text-text-secondary hover:bg-background hover:text-red-500"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="mb-1 block text-sm font-medium text-text">
                          Name
                        </label>
                        <input
                          type="text"
                          value={variable.name}
                          onChange={(e) => handleVariableChange(index, 'name', e.target.value)}
                          className="w-full rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                          placeholder="e.g., api_key"
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
                          placeholder="e.g., API key for external service"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="mb-4 flex items-center space-x-2 text-base font-medium text-text">
                <FileText className="h-5 w-5" />
                <span>Content Buckets</span>
              </h3>
              <div className="space-y-4">
                {mockContentBuckets.map((bucket) => (
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
              <div className="mb-4 flex items-center justify-between">
                <label className="text-sm font-medium text-text">
                  Team Agents ({selectedAgents.length}/5)
                </label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAgentSelect(true)}
                  disabled={selectedAgents.length >= 5}
                >
                  Add Agent
                </Button>
              </div>

              <div className="space-y-2">
                {selectedAgents.map((agent) => (
                  <div
                    key={agent.id}
                    className="flex items-center justify-between rounded-lg border border-border bg-background-secondary p-3"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <div className="font-medium text-text">{agent.name}</div>
                        <div className="text-sm text-text-secondary">
                          {agent.description}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveAgent(agent.id)}
                      className="text-text-secondary hover:text-text"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}

                {selectedAgents.length === 0 && (
                  <div className="rounded-lg border border-border bg-background-secondary p-4 text-center text-text-secondary">
                    No agents selected
                  </div>
                )}
              </div>
            </div>
          </div>

          {showAgentSelect && (
            <div className="fixed inset-x-0 bottom-0 top-1/4 z-10 rounded-t-xl border border-border bg-background shadow-lg">
              <div className="flex h-full flex-col">
                <div className="flex items-center justify-between border-b border-border p-4">
                  <h3 className="text-lg font-medium text-text">Select Agent</h3>
                  <button
                    onClick={() => {
                      setShowAgentSelect(false);
                      setSearchQuery('');
                    }}
                    className="rounded-md p-1 hover:bg-background-secondary"
                  >
                    <X className="h-5 w-5 text-text-secondary" />
                  </button>
                </div>

                <div className="p-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
                    <input
                      type="text"
                      placeholder="Search agents..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full rounded-md border border-border bg-background pl-10 pr-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      autoFocus
                    />
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                  <div className="grid grid-cols-2 gap-4">
                    {filteredAgents.map((agent) => (
                      <button
                        key={agent.id}
                        onClick={() => handleAgentSelect(agent)}
                        className="flex items-start space-x-3 rounded-lg border border-border p-3 text-left transition-colors hover:border-primary"
                      >
                        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary/10">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <div className="font-medium text-text">{agent.name}</div>
                          <div className="mt-1 text-sm text-text-secondary">
                            {agent.description}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-border p-6">
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={
                !name.trim() || 
                !description.trim() || 
                selectedAgents.length === 0 ||
                variables.some(v => !v.name.trim() || !v.description.trim())
              }
            >
              Create team
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateTeamModal;