import React from 'react';
import { Globe, GitBranch, Code, Route, Play, Square, Bot } from 'lucide-react';

interface NodeType {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: string;
}

const nodeTypes: NodeType[] = [
  {
    id: 'start',
    name: 'Start',
    description: 'Starting point of the workflow',
    icon: <Play className="h-5 w-5 text-emerald-500" />,
    category: 'Flow Control'
  },
  {
    id: 'decision',
    name: 'Decision',
    description: 'Branch based on conditions',
    icon: <GitBranch className="h-5 w-5 text-amber-500" />,
    category: 'Flow Control'
  },
  {
    id: 'api',
    name: 'API',
    description: 'Make API requests',
    icon: <Globe className="h-5 w-5 text-purple-500" />,
    category: 'Integration'
  },
  {
    id: 'function',
    name: 'Function',
    description: 'Run custom JavaScript code',
    icon: <Code className="h-5 w-5 text-orange-500" />,
    category: 'Core'
  },
  {
    id: 'agent',
    name: 'Agent',
    description: 'Add an AI agent to your workflow',
    icon: <Bot className="h-5 w-5 text-primary" />,
    category: 'AI'
  },
  {
    id: 'router',
    name: 'Router',
    description: 'Route to different paths',
    icon: <Route className="h-5 w-5 text-blue-500" />,
    category: 'Flow Control'
  },
  {
    id: 'end',
    name: 'End',
    description: 'End point of the workflow',
    icon: <Square className="h-5 w-5 text-red-500" />,
    category: 'Flow Control'
  }
];

interface NodeListProps {
  searchQuery?: string;
}

const NodeList: React.FC<NodeListProps> = ({ searchQuery = '' }) => {
  const filteredNodes = nodeTypes.filter(node =>
    node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    node.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="space-y-2">
      {filteredNodes.map((node) => (
        <div
          key={node.id}
          draggable
          onDragStart={(e) => onDragStart(e, node.id)}
          className="flex cursor-grab items-center space-x-3 rounded-lg border border-border bg-background p-3 transition-colors hover:border-primary"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background-secondary">
            {node.icon}
          </div>
          <div>
            <h3 className="font-medium text-text">{node.name}</h3>
            <p className="text-sm text-text-secondary">{node.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NodeList;