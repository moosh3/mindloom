import React, { useState, useCallback } from 'react';
import ReactFlow, { 
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Connection,
  addEdge,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Plus, Play, Save } from 'lucide-react';
import Button from '../components/ui/Button';
import WorkflowNodeTypes from '../components/workflow/WorkflowNodeTypes';
import { Agent } from '../types';

interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: Node[];
  edges: Edge[];
  createdAt: Date;
}

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'trigger',
    position: { x: 250, y: 100 },
    data: { label: 'Start' }
  }
];

const Workflows: React.FC = () => {
  const [workflows] = useState<Workflow[]>([
    {
      id: '1',
      name: 'Customer Support Pipeline',
      description: 'Automated support ticket processing workflow',
      nodes: initialNodes,
      edges: [],
      createdAt: new Date(2024, 0, 15)
    }
  ]);

  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);

  const onNodesChange = useCallback((changes: any) => {
    setNodes((nds) => {
      const newNodes = [...nds];
      changes.forEach((change: any) => {
        const nodeIndex = newNodes.findIndex((n) => n.id === change.id);
        if (nodeIndex !== -1) {
          newNodes[nodeIndex] = { ...newNodes[nodeIndex], ...change };
        }
      });
      return newNodes;
    });
  }, []);

  const onEdgesChange = useCallback((changes: any) => {
    setEdges((eds) => {
      const newEdges = [...eds];
      changes.forEach((change: any) => {
        const edgeIndex = newEdges.findIndex((e) => e.id === change.id);
        if (edgeIndex !== -1) {
          newEdges[edgeIndex] = { ...newEdges[edgeIndex], ...change };
        }
      });
      return newEdges;
    });
  }, []);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    []
  );

  const addNode = (type: string) => {
    const newNode: Node = {
      id: (nodes.length + 1).toString(),
      type,
      position: { x: 250, y: (nodes.length + 1) * 100 },
      data: { label: type.charAt(0).toUpperCase() + type.slice(1) }
    };
    setNodes([...nodes, newNode]);
  };

  return (
    <div className="flex h-full flex-col bg-background">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="text-xl font-semibold text-text">Workflows</h1>
        <div className="flex space-x-3">
          <Button variant="outline" icon={<Save className="h-4 w-4" />}>
            Save
          </Button>
          <Button variant="outline" icon={<Play className="h-4 w-4" />}>
            Run
          </Button>
          <Button variant="primary" icon={<Plus className="h-4 w-4" />}>
            Create workflow
          </Button>
        </div>
      </div>

      <div className="flex flex-1">
        <div className="w-64 border-r border-border bg-background p-4">
          <h2 className="mb-4 text-sm font-medium text-text">Add Node</h2>
          <div className="space-y-2">
            <button
              onClick={() => addNode('agent')}
              className="flex w-full items-center space-x-2 rounded-md border border-border p-2 text-sm hover:border-primary"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
                <Plus className="h-4 w-4 text-primary" />
              </div>
              <span>Agent</span>
            </button>
            <button
              onClick={() => addNode('team')}
              className="flex w-full items-center space-x-2 rounded-md border border-border p-2 text-sm hover:border-primary"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
                <Plus className="h-4 w-4 text-primary" />
              </div>
              <span>Team</span>
            </button>
            <button
              onClick={() => addNode('condition')}
              className="flex w-full items-center space-x-2 rounded-md border border-border p-2 text-sm hover:border-primary"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
                <Plus className="h-4 w-4 text-primary" />
              </div>
              <span>Condition</span>
            </button>
          </div>
        </div>

        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={WorkflowNodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
};

export default Workflows;