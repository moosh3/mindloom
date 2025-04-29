import React from 'react';
import { Handle, Position } from 'reactflow';
import { Settings } from 'lucide-react';

const ProcessNode = ({ data }: { data: any }) => {
  return (
    <div className="px-4 py-2 shadow-lg rounded-md bg-white border-2 border-blue-500">
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      <div className="flex items-center">
        <Settings className="w-4 h-4 text-blue-500 mr-2" />
        <div className="text-sm font-medium">{data.label || 'Process'}</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
};

export default ProcessNode;