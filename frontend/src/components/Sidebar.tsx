import React, { useState } from 'react';
import { 
  Users,
  MessageSquare, 
  FileText,
  PlayCircle,
  Bot, 
  Menu,
  LogOut
} from 'lucide-react';
import AgentSelect from './AgentSelect';
import { Agent } from '../types';
import { useAuthStore } from '../stores/authStore';
import AuthModal from './auth/AuthModal';

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
  onStartChat?: (agent: Agent) => void;
  onNavigate: (view: 'dashboard' | 'chat' | 'content' | 'runs' | 'teams') => void;
  currentView: string;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  collapsed = false, 
  onToggle, 
  onStartChat,
  onNavigate,
  currentView
}) => {
  const [showAgentSelect, setShowAgentSelect] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { user, signOut } = useAuthStore();
  
  const navigation = [
    { name: 'Agents', icon: Bot, href: 'dashboard', current: currentView === 'dashboard' },
    { name: 'Teams', icon: Users, href: 'teams', current: currentView === 'teams' },
    { name: 'Chat', icon: MessageSquare, href: 'chat', current: currentView === 'chat' },
    { name: 'Content', icon: FileText, href: 'content', current: currentView === 'content' },
    { name: 'Runs', icon: PlayCircle, href: 'runs', current: currentView === 'runs' },
  ];
  
  const handleAgentSelect = (agent: Agent) => {
    setShowAgentSelect(false);
    if (onStartChat) {
      onStartChat(agent);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };
  
  return (
    <div className={`flex h-screen flex-col border-r border-border bg-background transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}>
      <div className="flex h-16 items-center justify-between px-4">
        {!collapsed && (
          <div className="text-xl font-bold text-primary">AgnoAgents</div>
        )}
        <button onClick={onToggle} className="rounded-md p-1 hover:bg-background-secondary">
          <Menu className="h-5 w-5 text-text-secondary" />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <nav className="space-y-1">
          {navigation.map((item) => (
            <button
              key={item.name}
              onClick={() => onNavigate(item.href as 'dashboard' | 'chat' | 'content' | 'runs' | 'teams')}
              className={`
                flex w-full items-center rounded-md px-3 py-2 text-sm font-medium transition-colors
                ${item.current
                  ? 'bg-background-secondary text-primary'
                  : 'text-text-secondary hover:bg-background-secondary hover:text-primary'
                }
              `}
            >
              <item.icon
                className={`h-5 w-5 flex-shrink-0 ${
                  item.current ? 'text-primary' : 'text-text-secondary'
                }`}
              />
              {!collapsed && <span className="ml-3">{item.name}</span>}
            </button>
          ))}
        </nav>
      </div>
      
      <div className="flex items-center space-x-3 border-t border-border p-4">
        {user ? (
          <>
            <div className="flex-shrink-0">
              <img
                className="h-9 w-9 rounded-full"
                src={user.avatar_url || "https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2"}
                alt={user.name}
              />
            </div>
            {!collapsed && (
              <>
                <div className="flex-1">
                  <p className="text-sm font-medium text-text">{user.name}</p>
                  <p className="text-xs text-text-secondary">{user.email}</p>
                </div>
                <button
                  onClick={handleSignOut}
                  className="rounded-md p-1 text-text-secondary hover:bg-background-secondary hover:text-primary"
                >
                  <LogOut className="h-5 w-5" />
                </button>
              </>
            )}
          </>
        ) : (
          <button
            onClick={() => setShowAuthModal(true)}
            className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:bg-primary-light"
          >
            Sign In
          </button>
        )}
      </div>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />

      {showAgentSelect && (
        <AgentSelect
          onSelect={handleAgentSelect}
          onClose={() => setShowAgentSelect(false)}
        />
      )}
    </div>
  );
};

export default Sidebar;