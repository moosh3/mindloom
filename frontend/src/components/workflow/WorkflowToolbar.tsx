import React, { useState } from 'react';
import * as Popover from '@radix-ui/react-popover';
import * as Tooltip from '@radix-ui/react-tooltip';
import {
  Play,
  Bug,
  History,
  Bell,
  Upload,
  Edit2,
  Save,
  RotateCcw,
  RotateCw,
  ChevronDown,
} from 'lucide-react';
import { useWorkflowStore } from '../../stores/workflowStore';

const WorkflowToolbar: React.FC = () => {
  const {
    workflowName,
    setWorkflowName,
    debugMode,
    setDebugMode,
    isRunning,
    setIsRunning,
    undo,
    redo,
  } = useWorkflowStore();

  const [isEditing, setIsEditing] = useState(false);
  const [tempName, setTempName] = useState(workflowName);

  const handleNameSubmit = () => {
    setWorkflowName(tempName);
    setIsEditing(false);
  };

  return (
    <div className="h-14 bg-background border-b border-border flex items-center justify-between px-4">
      <div className="flex items-center space-x-4">
        {isEditing ? (
          <input
            type="text"
            value={tempName}
            onChange={(e) => setTempName(e.target.value)}
            onBlur={handleNameSubmit}
            onKeyDown={(e) => e.key === 'Enter' && handleNameSubmit()}
            className="bg-background-secondary text-text px-3 py-1 rounded-md border border-border focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            autoFocus
          />
        ) : (
          <div className="flex items-center space-x-2">
            <h1 className="text-text font-medium">{workflowName}</h1>
            <button
              onClick={() => setIsEditing(true)}
              className="text-text-secondary hover:text-text"
            >
              <Edit2 size={16} />
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center">
        <div className="flex items-center space-x-6 mr-6">
          <Tooltip.Provider>
            <Tooltip.Root>
              <Tooltip.Trigger asChild>
                <button
                  onClick={() => setDebugMode(!debugMode)}
                  className="text-text-secondary hover:text-text"
                >
                  <Bug size={20} />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  className="bg-background text-text text-sm px-2 py-1 rounded border border-border"
                  sideOffset={5}
                >
                  Debug Mode
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>

            <Tooltip.Root>
              <Tooltip.Trigger asChild>
                <button
                  onClick={undo}
                  className="text-text-secondary hover:text-text"
                >
                  <RotateCcw size={20} />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  className="bg-background text-text text-sm px-2 py-1 rounded border border-border"
                  sideOffset={5}
                >
                  Undo
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>

            <Tooltip.Root>
              <Tooltip.Trigger asChild>
                <button
                  onClick={redo}
                  className="text-text-secondary hover:text-text"
                >
                  <RotateCw size={20} />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  className="bg-background text-text text-sm px-2 py-1 rounded border border-border"
                  sideOffset={5}
                >
                  Redo
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>

            <Tooltip.Root>
              <Tooltip.Trigger asChild>
                <button className="text-text-secondary hover:text-text">
                  <Bell size={20} />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  className="bg-background text-text text-sm px-2 py-1 rounded border border-border"
                  sideOffset={5}
                >
                  Notifications
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>

            <Tooltip.Root>
              <Tooltip.Trigger asChild>
                <button className="text-text-secondary hover:text-text">
                  <Upload size={20} />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  className="bg-background text-text text-sm px-2 py-1 rounded border border-border"
                  sideOffset={5}
                >
                  Deploy as API
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>

            <Tooltip.Root>
              <Tooltip.Trigger asChild>
                <button className="text-text-secondary hover:text-text">
                  <Save size={20} />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  className="bg-background text-text text-sm px-2 py-1 rounded border border-border"
                  sideOffset={5}
                >
                  Save Workflow
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>
          </Tooltip.Provider>
        </div>

        <button
          onClick={() => setIsRunning(!isRunning)}
          className={`
            flex items-center space-x-2 px-4 py-2 rounded-md text-white font-medium
            ${isRunning ? 'bg-primary-dark hover:bg-primary' : 'bg-primary hover:bg-primary-light'}
          `}
        >
          <Play size={20} />
          <span>Run</span>
          <ChevronDown size={16} />
        </button>
      </div>
    </div>
  );
};

export default WorkflowToolbar;