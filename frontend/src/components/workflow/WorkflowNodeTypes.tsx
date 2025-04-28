import React, { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { Bot, Users, GitBranch, Play, ChevronDown } from 'lucide-react';
import { Agent } from '../../types';
import { agentTemplates, userAgents } from '../../utils/data';

const baseNodeStyles = "px-4 py-2 rounded-lg shadow-md border min-w-[150px]";

interface NodeData {
  label: string;
  agent?: Agent;
  team?: {
    id: string;
    name: string;
  };
}

const TriggerNode = ({ data }: { data: NodeData }) => (
  <div className={`${baseNodeStyles} bg-green-50 border-green-200`}>
    <Handle type="source" position={Position.Bottom} />
    <div className="flex items-center space-x-2">
      <Play className="h-4 w-4 text-green-500" />
      <span className="text-sm font-medium text-green-700">{data.label}</span>
    </div>
  </div>
);

const AgentNode = ({ data }: { data: NodeData }) => {
  const [showSelect, setShowSelect] = useState(false);
  const allAgents = [...agentTemplates, ...userAgents];

  return (
    <div className="relative">
      <div className={`${baseNodeStyles} bg-blue-50 border-blue-200`}>
        <Handle type="target" position={Position.Top} />
        <button 
          onClick={() => setShowSelect(!showSelect)}
          className="flex items-center justify-between w-full"
        >
          <div className="flex items-center space-x-2">
            <Bot className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-medium text-blue-700">
              {data.agent?.name || "Select Agent"}
            </span>
          </div>
          <ChevronDown className="h-4 w-4 text-blue-500" />
        </button>
        <Handle type="source" position={Position.Bottom} />
      </div>

      {showSelect && (
        <div className="absolute z-10 mt-1 w-64 rounded-md border border-border bg-white shadow-lg">
          <div className="max-h-48 overflow-y-auto p-1">
            {allAgents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => {
                  data.agent = agent;
                  setShowSelect(false);
                }}
                className="flex w-full items-center space-x-2 rounded-md px-3 py-2 text-left text-sm hover:bg-blue-50"
              >
                <Bot className="h-4 w-4 text-blue-500" />
                <div>
                  <div className="font-medium text-gray-900">{agent.name}</div>
                  <div className="text-xs text-gray-500">{agent.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const TeamNode = ({ data }: { data: NodeData }) => {
  const [showSelect, setShowSelect] = useState(false);
  const teams = [
    { id: '1', name: 'Customer Support' },
    { id: '2', name: 'Sales Operations' },
    { id: '3', name: 'Engineering' }
  ];

  return (
    <div className="relative">
      <div className={`${baseNodeStyles} bg-purple-50 border-purple-200`}>
        <Handle type="target" position={Position.Top} />
        <button 
          onClick={() => setShowSelect(!showSelect)}
          className="flex items-center justify-between w-full"
        >
          <div className="flex items-center space-x-2">
            <Users className="h-4 w-4 text-purple-500" />
            <span className="text-sm font-medium text-purple-700">
              {data.team?.name || "Select Team"}
            </span>
          </div>
          <ChevronDown className="h-4 w-4 text-purple-500" />
        </button>
        <Handle type="source" position={Position.Bottom} />
      </div>

      {showSelect && (
        <div className="absolute z-10 mt-1 w-64 rounded-md border border-border bg-white shadow-lg">
          <div className="max-h-48 overflow-y-auto p-1">
            {teams.map((team) => (
              <button
                key={team.id}
                onClick={() => {
                  data.team = team;
                  setShowSelect(false);
                }}
                className="flex w-full items-center space-x-2 rounded-md px-3 py-2 text-left text-sm hover:bg-purple-50"
              >
                <Users className="h-4 w-4 text-purple-500" />
                <div className="font-medium text-gray-900">{team.name}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const ConditionNode = ({ data }: { data: NodeData }) => (
  <div className={`${baseNodeStyles} bg-yellow-50 border-yellow-200`}>
    <Handle type="target" position={Position.Top} />
    <div className="flex items-center space-x-2">
      <GitBranch className="h-4 w-4 text-yellow-500" />
      <span className="text-sm font-medium text-yellow-700">{data.label}</span>
    </div>
    <Handle type="source" position={Position.Bottom} id="a" />
    <Handle type="source" position={Position.Right} id="b" />
  </div>
);

const nodeTypes = {
  trigger: TriggerNode,
  agent: AgentNode,
  team: TeamNode,
  condition: ConditionNode,
};

export default nodeTypes;