import React, { useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { Search } from 'lucide-react';
import NodeList from './NodeList';
import ToolList from './ToolList';

const WorkflowSidebar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="w-64 bg-background border-r border-border flex flex-col">
      <div className="p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary" size={16} />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-background-secondary text-text pl-10 pr-4 py-2 rounded-md text-sm border border-border focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      <Tabs.Root defaultValue="blocks" className="flex-1">
        <Tabs.List className="flex border-b border-border">
          <Tabs.Trigger
            value="blocks"
            className="flex-1 px-4 py-2 text-sm text-text-secondary hover:text-text data-[state=active]:text-text data-[state=active]:border-b-2 data-[state=active]:border-primary"
          >
            Blocks
          </Tabs.Trigger>
          <Tabs.Trigger
            value="tools"
            className="flex-1 px-4 py-2 text-sm text-text-secondary hover:text-text data-[state=active]:text-text data-[state=active]:border-b-2 data-[state=active]:border-primary"
          >
            Tools
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="blocks" className="flex-1 overflow-y-auto p-4">
          <NodeList searchQuery={searchQuery} />
        </Tabs.Content>

        <Tabs.Content value="tools" className="flex-1 overflow-y-auto p-4">
          <ToolList searchQuery={searchQuery} />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
};

export default WorkflowSidebar;