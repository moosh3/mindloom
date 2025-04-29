import React from 'react';
import { Handle, Position } from 'reactflow';
import { Square } from 'lucide-react';

const EndNode = ({ data, selected }: { data: any; selected: boolean }) => {
  return (
    <div className="relative">
      <div className={`min-w-[200px] rounded-lg border ${selected ? 'border-primary' : 'border-border'} bg-background p-4 shadow-lg`}>
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-red-500/10">
            <Square className="h-4 w-4 text-red-500" />
          </div>
          <span className="text-sm font-medium text-text">{data.label || 'End'}</span>
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Top}
        className="!border-border !bg-background-secondary"
      />
    </div>
  );
};

export default EndNode;