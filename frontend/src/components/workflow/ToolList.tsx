import React from 'react';
import { FileText, Globe, Database, Code, Bot, Search } from 'lucide-react';

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: string;
}

const tools: Tool[] = [
  {
    id: 'airtable',
    name: 'Airtable',
    description: 'Read, create, and update Airtable',
    icon: <Database className="h-5 w-5 text-blue-500" />,
    category: 'Database'
  },
  {
    id: 'browser',
    name: 'Browser Use',
    description: 'Run browser automation tasks',
    icon: <Globe className="h-5 w-5 text-purple-500" />,
    category: 'Automation'
  },
  {
    id: 'confluence',
    name: 'Confluence',
    description: 'Interact with Confluence',
    icon: <FileText className="h-5 w-5 text-blue-500" />,
    category: 'Documentation'
  },
  {
    id: 'evaluator',
    name: 'Evaluator',
    description: 'Evaluate content',
    icon: <Code className="h-5 w-5 text-green-500" />,
    category: 'Analysis'
  },
  {
    id: 'exa',
    name: 'Exa',
    description: 'Search with Exa AI',
    icon: <Bot className="h-5 w-5 text-indigo-500" />,
    category: 'AI'
  },
  {
    id: 'firecrawl',
    name: 'Firecrawl',
    description: 'Scrape website content',
    icon: <Search className="h-5 w-5 text-orange-500" />,
    category: 'Data Collection'
  }
];

const ToolList: React.FC = () => {
  return (
    <div className="space-y-2">
      {tools.map((tool) => (
        <div
          key={tool.id}
          className="flex cursor-pointer items-center space-x-3 rounded-lg border border-border bg-background p-3 transition-colors hover:border-primary"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background-secondary">
            {tool.icon}
          </div>
          <div>
            <h3 className="font-medium text-text">{tool.name}</h3>
            <p className="text-sm text-text-secondary">{tool.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ToolList;