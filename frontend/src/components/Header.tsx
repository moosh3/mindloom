import React from 'react';
import { Info, Plus } from 'lucide-react';
import Button from './ui/Button';

interface HeaderProps {
  onCreateAgent: () => void;
  onHelpClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onCreateAgent, onHelpClick }) => {
  return (
    <div className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-drw-dark-lighter bg-drw-dark px-6">
      <h1 className="text-xl font-semibold text-drw-gold">Agents</h1>
      <div className="flex items-center space-x-4">
        <button 
          onClick={onHelpClick}
          className="text-sm font-medium text-drw-gold hover:text-drw-gold-light"
        >
          How agents work
        </button>
        <Button 
          variant="primary" 
          icon={<Plus className="h-4 w-4" />}
          onClick={onCreateAgent}
        >
          Create agent
        </Button>
      </div>
    </div>
  );
};

export default Header;