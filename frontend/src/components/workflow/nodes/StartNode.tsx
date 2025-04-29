import React, { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { Play, Clock, Globe, ChevronDown } from 'lucide-react';

interface StartNodeData {
  triggerType: 'manual' | 'webhook' | 'schedule';
  webhookUrl?: string;
  schedule?: string;
  label?: string;
}

const StartNode = ({ data }: { data: StartNodeData }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getTriggerIcon = (type: StartNodeData['triggerType']) => {
    switch (type) {
      case 'webhook':
        return <Globe className="h-4 w-4 text-primary" />;
      case 'schedule':
        return <Clock className="h-4 w-4 text-primary" />;
      default:
        return <Play className="h-4 w-4 text-primary" />;
    }
  };

  const getTriggerLabel = (type: StartNodeData['triggerType']) => {
    switch (type) {
      case 'webhook':
        return 'On webhook call';
      case 'schedule':
        return 'On schedule';
      default:
        return 'Run manually';
    }
  };

  return (
    <div className="relative">
      <div className="min-w-[240px] rounded-lg border border-border bg-background shadow-lg">
        <div className="flex items-center space-x-3 border-b border-border p-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary/10">
            <Play className="h-4 w-4 text-primary" />
          </div>
          <span className="text-sm font-medium text-text">Start Workflow</span>
        </div>
        
        <div className="p-3">
          <div className="relative">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="flex w-full items-center justify-between rounded border border-border bg-background-secondary px-3 py-2 text-sm text-text hover:bg-background-tertiary"
            >
              <div className="flex items-center space-x-2">
                {getTriggerIcon(data.triggerType)}
                <span>{getTriggerLabel(data.triggerType)}</span>
              </div>
              <ChevronDown className={`h-4 w-4 text-text-secondary transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
              <div className="absolute left-0 right-0 top-full z-10 mt-1 overflow-hidden rounded-md border border-border bg-background shadow-xl">
                <div className="py-1">
                  <button
                    onClick={() => {
                      data.triggerType = 'manual';
                      setIsOpen(false);
                    }}
                    className="flex w-full items-center space-x-2 px-3 py-2 text-sm text-text hover:bg-background-secondary"
                  >
                    <Play className="h-4 w-4 text-primary" />
                    <span>Run manually</span>
                  </button>
                  <button
                    onClick={() => {
                      data.triggerType = 'webhook';
                      setIsOpen(false);
                    }}
                    className="flex w-full items-center space-x-2 px-3 py-2 text-sm text-text hover:bg-background-secondary"
                  >
                    <Globe className="h-4 w-4 text-primary" />
                    <span>On webhook call</span>
                  </button>
                  <button
                    onClick={() => {
                      data.triggerType = 'schedule';
                      setIsOpen(false);
                    }}
                    className="flex w-full items-center space-x-2 px-3 py-2 text-sm text-text hover:bg-background-secondary"
                  >
                    <Clock className="h-4 w-4 text-primary" />
                    <span>On schedule</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!border-border !bg-background-secondary"
      />
    </div>
  );
};

export default StartNode;