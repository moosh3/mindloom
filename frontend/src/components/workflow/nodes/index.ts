import { NodeTypes } from 'reactflow';
import StartNode from './StartNode';
import DecisionNode from './DecisionNode';
import EndNode from './EndNode';
import APINode from './APINode';
import FunctionNode from './FunctionNode';
import RouterNode from './RouterNode';
import AgentNode from './AgentNode';

export const nodeTypes: NodeTypes = {
  start: StartNode,
  decision: DecisionNode,
  end: EndNode,
  api: APINode,
  function: FunctionNode,
  router: RouterNode,
  agent: AgentNode,
};

export const nodeConfig = {
  start: {
    label: 'Start',
    description: 'Starting point of the workflow',
    color: 'emerald',
    icon: 'Play',
    data: {
      triggerType: 'manual',
    },
  },
  decision: {
    label: 'Decision',
    description: 'Branch based on conditions',
    color: 'amber',
    icon: 'GitBranch',
    data: {
      conditions: [
        { id: '1', condition: '' }
      ]
    }
  },
  end: {
    label: 'End',
    description: 'End point of the workflow',
    color: 'red',
    icon: 'Square',
    data: {}
  },
  api: {
    label: 'API',
    description: 'Make API requests',
    color: 'purple',
    icon: 'Globe',
    data: {
      url: '',
      method: 'GET',
      queryParams: [],
      headers: [],
      body: ''
    }
  },
  function: {
    label: 'Function',
    description: 'Run custom JavaScript code',
    color: 'orange',
    icon: 'Code',
    data: {
      code: 'def process(input):\n    # Your code here\n    return input'
    }
  },
  agent: {
    label: 'Agent',
    description: 'Add an AI agent to your workflow',
    color: 'indigo',
    icon: 'Bot',
    data: {
      systemPrompt: '',
      userPrompt: '',
      model: '',
      temperature: 1,
      apiKey: '',
      tools: [],
      responseFormat: ''
    }
  },
  router: {
    label: 'Router',
    description: 'Route to different paths',
    color: 'blue',
    icon: 'Route',
    data: {}
  },
};