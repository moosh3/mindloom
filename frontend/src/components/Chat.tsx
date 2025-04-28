import React, { useState, useEffect } from 'react';
import { Send, ArrowLeft, Bot, ChevronDown, Plus, Search, Trash2 } from 'lucide-react';
import { Agent } from '../types';
import { agentIconMap } from '../utils/data';
import AgentSelect from './AgentSelect';
import Button from './ui/Button';
import useChatStore from '../stores/chatStore';

interface ChatProps {
  agent: Agent;
  onBack: () => void;
}

const Chat: React.FC<ChatProps> = ({ agent: initialAgent, onBack }) => {
  const [message, setMessage] = useState('');
  const [agent, setAgent] = useState(initialAgent);
  const [showAgentSelect, setShowAgentSelect] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAgentSearch, setShowAgentSearch] = useState(false);

  const {
    conversations,
    currentConversation,
    addConversation,
    addMessage,
    setCurrentConversation,
    clearConversation,
  } = useChatStore();

  useEffect(() => {
    // Find existing conversation or create new one
    const existingConversation = conversations.find(c => c.agentId === agent.id);
    if (existingConversation) {
      setCurrentConversation(existingConversation.id);
    } else {
      const newConversation = addConversation(agent);
      addMessage(newConversation.id, {
        content: `Hi! I'm your ${agent.name.toLowerCase()}. How can I help you today?`,
        sender: 'agent',
        timestamp: new Date(),
      });
    }
  }, [agent.id]);

  const IconComponent = agentIconMap[agent.icon] || agentIconMap.default;

  const handleSendMessage = () => {
    if (!message.trim() || !currentConversation) return;

    // Add user message
    addMessage(currentConversation.id, {
      content: message,
      sender: 'user',
      timestamp: new Date(),
    });

    // Simulate agent response
    setTimeout(() => {
      addMessage(currentConversation.id, {
        content: `I understand you're asking about "${message}". Let me help you with that.`,
        sender: 'agent',
        timestamp: new Date(),
      });
    }, 1000);

    setMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleAgentSelect = (newAgent: Agent) => {
    setAgent(newAgent);
    setShowAgentSelect(false);
    setShowAgentSearch(false);
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
    }).format(date);
  };

  return (
    <div className="flex h-full">
      {/* Left Sidebar */}
      <div className="w-80 flex-shrink-0 border-r border-border bg-background">
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          <h2 className="text-lg font-semibold text-text">Chat History</h2>
          <Button
            variant="primary"
            size="sm"
            icon={<Plus className="h-4 w-4" />}
            onClick={() => setShowAgentSearch(true)}
          >
            New Chat
          </Button>
        </div>
        
        {showAgentSearch ? (
          <div className="flex h-[calc(100vh-4rem)] flex-col">
            <div className="p-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
                <input
                  type="text"
                  placeholder="Search agents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-md border border-border bg-background pl-10 pr-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  autoFocus
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 pt-0">
              <AgentSelect
                onSelect={handleAgentSelect}
                onClose={() => setShowAgentSearch(false)}
              />
            </div>
          </div>
        ) : (
          <div className="h-[calc(100vh-4rem)] overflow-y-auto p-4">
            <div className="space-y-2">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => {
                    setCurrentConversation(conversation.id);
                    const conversationAgent = conversation.agentId === agent.id ? agent : null;
                    if (conversationAgent) {
                      setAgent(conversationAgent);
                    }
                  }}
                  className={`flex w-full items-center space-x-3 rounded-lg border p-3 text-left transition-colors ${
                    currentConversation?.id === conversation.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-background-secondary">
                    <IconComponent className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <p className="truncate text-sm font-medium text-text">
                        {conversation.title}
                      </p>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          clearConversation(conversation.id);
                        }}
                        className="rounded-full p-1 hover:bg-background-secondary"
                      >
                        <Trash2 className="h-4 w-4 text-text-secondary" />
                      </button>
                    </div>
                    {conversation.lastMessage && (
                      <p className="mt-1 truncate text-xs text-text-secondary">
                        {conversation.lastMessage}
                      </p>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col bg-background">
        <div className="flex items-center border-b border-border px-4 py-3">
          <button
            onClick={onBack}
            className="mr-3 rounded-md p-1 hover:bg-background-secondary"
          >
            <ArrowLeft className="h-5 w-5 text-text-secondary" />
          </button>
          <button
            onClick={() => setShowAgentSelect(!showAgentSelect)}
            className="flex flex-1 items-center space-x-3 rounded-md py-1 hover:bg-background-secondary"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-background-secondary">
              <IconComponent className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1">
              <h2 className="text-sm font-medium text-text">{agent.name}</h2>
              <p className="text-xs text-text-secondary">{agent.description}</p>
            </div>
            <ChevronDown className="h-4 w-4 text-text-secondary" />
          </button>

          {showAgentSelect && (
            <div className="absolute left-0 right-0 top-full z-50 mt-1 px-4">
              <AgentSelect
                onSelect={handleAgentSelect}
                onClose={() => setShowAgentSelect(false)}
              />
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-4">
            {currentConversation?.messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start space-x-3 ${
                  msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-background-secondary">
                  {msg.sender === 'user' ? (
                    <div className="h-6 w-6 rounded-full bg-cover bg-center" style={{ backgroundImage: 'url(https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2)' }} />
                  ) : (
                    <IconComponent className="h-4 w-4 text-primary" />
                  )}
                </div>
                <div className={`rounded-lg p-4 ${
                  msg.sender === 'user' ? 'bg-primary text-white' : 'bg-background-secondary text-text'
                }`}>
                  <p className="text-sm">{msg.content}</p>
                  <span className="mt-1 block text-xs opacity-75">
                    {formatTime(msg.timestamp)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-border p-4">
          <div className="flex space-x-4">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              rows={1}
              className="flex-1 resize-none rounded-md border border-border bg-background px-4 py-2 text-sm text-text placeholder-text-tertiary focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <button
              onClick={handleSendMessage}
              disabled={!message.trim()}
              className="flex items-center justify-center rounded-md bg-primary px-4 py-2 text-white hover:bg-primary-light disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;