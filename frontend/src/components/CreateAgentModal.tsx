import React, { useState } from 'react';
import Button from './ui/Button';
import { Plus, X } from 'lucide-react';
import AgentCard from './AgentCard';
import { Agent } from '../types';
import FilterSidebar from './ui/FilterSidebar';
import { agentCategories, departmentCategories } from '../utils/data';

interface CreateAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateFromScratch: () => void;
  onTemplateSelect: (agent: Agent) => void;
  templates: Agent[];
}

const CreateAgentModal: React.FC<CreateAgentModalProps> = ({
  isOpen,
  onClose,
  onCreateFromScratch,
  onTemplateSelect,
  templates,
}) => {
  const [selectedCategory, setSelectedCategory] = useState('popular');
  
  if (!isOpen) return null;
  
  const filteredTemplates = templates.filter(
    template => template.category === selectedCategory
  );
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative max-h-[90vh] w-[90vw] max-w-5xl overflow-hidden rounded-xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-xl font-semibold text-gray-900">Create from a template</h2>
          <div className="flex space-x-2">
            <Button
              variant="primary"
              icon={<Plus className="h-4 w-4" />}
              onClick={onCreateFromScratch}
            >
              Create from scratch
            </Button>
            <button
              onClick={onClose}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-gray-100"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>
        </div>
        
        <div className="flex h-[calc(90vh-72px)] max-h-[700px]">
          <div className="border-r border-gray-200 pl-6">
            <FilterSidebar
              options={agentCategories}
              selectedOption={selectedCategory}
              onOptionSelect={setSelectedCategory}
            />
            <FilterSidebar
              options={departmentCategories}
              selectedOption={selectedCategory}
              onOptionSelect={setSelectedCategory}
            />
          </div>
          
          <div className="flex-1 overflow-y-auto p-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredTemplates.map((template) => (
                <AgentCard
                  key={template.id}
                  agent={template}
                  onClick={() => onTemplateSelect(template)}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateAgentModal;