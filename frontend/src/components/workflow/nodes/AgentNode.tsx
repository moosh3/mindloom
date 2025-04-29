import React, { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { Bot, Plus, Search } from 'lucide-react';
import Editor from '@monaco-editor/react';
import * as Select from '@radix-ui/react-select';
import * as Slider from '@radix-ui/react-slider';
import * as Popover from '@radix-ui/react-popover';

interface AgentNodeData {
  systemPrompt: string;
  userPrompt: string;
  model: string;
  temperature: number;
  apiKey: string;
  tools: string[];
  responseFormat: string;
}

const models = ['gpt-4o', 'gpt-4.1', 'gpt-4o-mini'];

const tools = [
  { id: 'airtable', name: 'Airtable', icon: '📊' },
  { id: 'browser', name: 'Browser Use', icon: '🌐' },
  { id: 'confluence', name: 'Confluence', icon: '📝' },
  { id: 'elevenlabs', name: 'ElevenLabs', icon: '🎧' },
  { id: 'evaluator', name: 'Evaluator', icon: '📊' },
  { id: 'exa', name: 'Exa', icon: '🔍' },
];

const AgentNode = ({ data, selected }: { data: AgentNodeData; selected: boolean }) => {
  const [isToolsOpen, setIsToolsOpen] = useState(false);
  const [toolSearch, setToolSearch] = useState('');
  const [selectedTools, setSelectedTools] = useState<string[]>(data.tools || []);
  const [temperature, setTemperature] = useState(data.temperature || 1);

  const filteredTools = tools.filter(tool =>
    tool.name.toLowerCase().includes(toolSearch.toLowerCase())
  );

  const handleToolSelect = (toolId: string) => {
    if (selectedTools.includes(toolId)) {
      setSelectedTools(selectedTools.filter(id => id !== toolId));
    } else {
      setSelectedTools([...selectedTools, toolId]);
    }
    data.tools = selectedTools;
  };

  const handleTemperatureChange = (value: number[]) => {
    const newTemp = value[0];
    setTemperature(newTemp);
    data.temperature = newTemp;
  };

  return (
    <div className="relative">
      <div className={`min-w-[300px] rounded-lg border ${selected ? 'border-primary' : 'border-border'} bg-background shadow-lg`}>
        <div className="flex items-center space-x-3 border-b border-border p-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary/10">
            <Bot className="h-4 w-4 text-primary" />
          </div>
          <span className="text-sm font-medium text-text">Agent</span>
        </div>

        <div className="space-y-4 p-4">
          {/* System Prompt */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              System Prompt
            </label>
            <textarea
              value={data.systemPrompt || ''}
              onChange={(e) => data.systemPrompt = e.target.value}
              placeholder="Enter system prompt..."
              rows={3}
              className="w-full rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none"
            />
          </div>

          {/* User Prompt */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              User Prompt
            </label>
            <textarea
              value={data.userPrompt || ''}
              onChange={(e) => data.userPrompt = e.target.value}
              placeholder="Enter context or user message..."
              rows={3}
              className="w-full rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none"
            />
          </div>

          {/* Model Selection */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              Model <span className="text-red-500">*</span>
            </label>
            <Select.Root value={data.model} onValueChange={(value) => data.model = value}>
              <Select.Trigger className="flex w-full items-center justify-between rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text">
                <Select.Value placeholder="Select a model" />
              </Select.Trigger>
              <Select.Portal>
                <Select.Content className="overflow-hidden rounded-md border border-border bg-background shadow-lg">
                  <Select.Viewport>
                    {models.map((model) => (
                      <Select.Item
                        key={model}
                        value={model}
                        className="cursor-pointer px-3 py-2 text-sm text-text outline-none hover:bg-background-secondary data-[highlighted]:bg-background-secondary"
                      >
                        <Select.ItemText>{model}</Select.ItemText>
                      </Select.Item>
                    ))}
                  </Select.Viewport>
                </Select.Content>
              </Select.Portal>
            </Select.Root>
          </div>

          {/* Temperature Slider */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-xs font-medium text-text-secondary">
                Temperature
              </label>
              <span className="text-xs text-text-secondary">
                {temperature.toFixed(1)}
              </span>
            </div>
            <Slider.Root
              className="relative flex h-5 w-full touch-none items-center"
              defaultValue={[temperature]}
              max={2}
              step={0.1}
              onValueChange={handleTemperatureChange}
            >
              <Slider.Track className="relative h-[3px] w-full grow rounded-full bg-background-tertiary">
                <Slider.Range className="absolute h-full rounded-full bg-primary" />
              </Slider.Track>
              <Slider.Thumb
                className="block h-4 w-4 rounded-full border border-primary bg-background shadow focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                aria-label="Temperature"
              />
            </Slider.Root>
          </div>

          {/* API Key */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              API Key <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              value={data.apiKey || ''}
              onChange={(e) => data.apiKey = e.target.value}
              placeholder="Enter your API key"
              className="w-full rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none"
            />
          </div>

          {/* Tools */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              Tools
            </label>
            <Popover.Root open={isToolsOpen} onOpenChange={setIsToolsOpen}>
              <Popover.Trigger asChild>
                <button className="flex w-full items-center justify-center space-x-1 rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text-secondary hover:bg-background-tertiary">
                  <Plus className="h-4 w-4" />
                  <span>Add Tool</span>
                </button>
              </Popover.Trigger>
              <Popover.Portal>
                <Popover.Content className="w-64 rounded-lg border border-border bg-background p-2 shadow-xl" sideOffset={5}>
                  <div className="relative mb-2">
                    <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
                    <input
                      type="text"
                      value={toolSearch}
                      onChange={(e) => setToolSearch(e.target.value)}
                      placeholder="Search tools..."
                      className="w-full rounded border border-border bg-background-secondary pl-8 pr-3 py-1.5 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    {filteredTools.map((tool) => (
                      <button
                        key={tool.id}
                        onClick={() => handleToolSelect(tool.id)}
                        className={`flex w-full items-center space-x-2 rounded px-2 py-1.5 text-sm ${
                          selectedTools.includes(tool.id)
                            ? 'bg-primary/20 text-primary'
                            : 'text-text hover:bg-background-secondary'
                        }`}
                      >
                        <span>{tool.icon}</span>
                        <span>{tool.name}</span>
                      </button>
                    ))}
                  </div>
                </Popover.Content>
              </Popover.Portal>
            </Popover.Root>
          </div>

          {/* Response Format */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              Response Format
            </label>
            <div className="rounded-lg border border-border bg-background-secondary">
              <Editor
                height="150px"
                defaultLanguage="json"
                theme="light"
                value={data.responseFormat || ''}
                onChange={(value) => data.responseFormat = value || ''}
                options={{
                  minimap: { enabled: false },
                  fontSize: 12,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  tabSize: 4,
                  lineHeight: 21,
                  folding: false,
                  glyphMargin: false,
                  automaticLayout: true,
                  padding: { top: 8, bottom: 8 },
                  lineNumbersMinChars: 2,
                  lineDecorationsWidth: 4,
                  renderLineHighlight: 'none',
                  overviewRulerBorder: false,
                  scrollbar: {
                    vertical: 'hidden',
                    horizontal: 'hidden'
                  },
                  overviewRulerLanes: 0
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Top}
        className="!border-border !bg-background-secondary"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!border-border !bg-background-secondary"
      />
    </div>
  );
};

export default AgentNode;