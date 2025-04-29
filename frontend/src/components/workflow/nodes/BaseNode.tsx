import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import * as Icons from 'lucide-react';
import { nodeConfig } from './index';

interface BaseNodeProps extends NodeProps {
  type: keyof typeof nodeConfig;
  data: {
    label?: string;
    inputs?: { id: string; label: string }[];
    outputs?: { id: string; label: string }[];
  };
}

const BaseNode: React.FC<BaseNodeProps> = ({ type, data, selected }) => {
  const config = nodeConfig[type];
  const Icon = Icons[config.icon as keyof typeof Icons];

  return (
    <div
      className={`
        group relative rounded-lg border bg-background p-4 transition-all
        ${selected ? 'border-primary shadow-lg' : 'border-border shadow-sm'}
      `}
    >
      {/* Input Attachment Bar */}
      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
        <div className="h-6 w-32 rounded-md bg-background-secondary border border-border group-hover:border-primary">
          <Handle
            type="target"
            position={Position.Top}
            style={{ 
              width: '100%',
              height: '100%',
              border: 'none',
              borderRadius: '6px',
              background: 'transparent'
            }}
          />
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <div className={`rounded-lg bg-${config.color}-100 p-2`}>
          <Icon className={`h-5 w-5 text-${config.color}-500`} />
        </div>
        <div>
          <h3 className="font-medium text-text">{data.label || config.label}</h3>
          <p className="text-sm text-text-secondary">{config.description}</p>
        </div>
      </div>

      {/* Output Attachment Bar */}
      <div className="absolute -bottom-3 left-1/2 -translate-x-1/2">
        <div className="h-6 w-32 rounded-md bg-background-secondary border border-border group-hover:border-primary">
          <Handle
            type="source"
            position={Position.Bottom}
            style={{ 
              width: '100%',
              height: '100%',
              border: 'none',
              borderRadius: '6px',
              background: 'transparent'
            }}
          />
        </div>
      </div>

      {/* Side Output Attachment Bar (for decision nodes) */}
      {type === 'decision' && (
        <div className="absolute -right-3 top-1/2 -translate-y-1/2">
          <div className="h-32 w-6 rounded-md bg-background-secondary border border-border group-hover:border-primary">
            <Handle
              type="source"
              position={Position.Right}
              id="side"
              style={{ 
                width: '100%',
                height: '100%',
                border: 'none',
                borderRadius: '6px',
                background: 'transparent'
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default BaseNode;