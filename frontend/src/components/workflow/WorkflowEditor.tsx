import React, { useCallback, useRef } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  ReactFlowInstance,
  ConnectionLineType,
} from 'reactflow';
import { useWorkflowStore } from '../../stores/workflowStore';
import WorkflowToolbar from './WorkflowToolbar';
import WorkflowSidebar from './WorkflowSidebar';
import { nodeTypes, nodeConfig } from './nodes';
import 'reactflow/dist/style.css';

const WorkflowEditor: React.FC = () => {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    setSelectedNode,
    setNodes,
  } = useWorkflowStore();

  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null);

  const handleNodeClick = useCallback((event: React.MouseEvent, node: any) => {
    setSelectedNode(node);
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowWrapper.current || !reactFlowInstance) return;

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: `${type}-${nodes.length + 1}`,
        type,
        position,
        data: { ...nodeConfig[type as keyof typeof nodeConfig].data },
      };

      setNodes([...nodes, newNode]);
    },
    [reactFlowInstance, nodes]
  );

  return (
    <div className="h-screen flex flex-col bg-background">
      <WorkflowToolbar />
      <div className="flex-1 flex">
        <WorkflowSidebar />
        <div 
          className="flex-1 relative" 
          ref={reactFlowWrapper}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={handleNodeClick}
            nodeTypes={nodeTypes}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            className="bg-background"
            minZoom={0.2}
            maxZoom={4}
            defaultViewport={{ x: 0, y: 0, zoom: 1.5 }}
            fitView={false}
            connectionLineType={ConnectionLineType.SmoothStep}
            connectionLineStyle={{
              stroke: '#d1d5db',
              strokeWidth: 2,
            }}
            defaultEdgeOptions={{
              type: 'smoothstep',
              style: {
                stroke: '#d1d5db',
                strokeWidth: 2,
              },
            }}
            snapToGrid={true}
            snapGrid={[16, 16]}
          >
            <Background color="#d1d5db" gap={16} />
            <Controls className="bg-white border-border" />
            <MiniMap
              className="bg-white border-border"
              nodeColor="#2563eb"
              maskColor="rgba(255, 255, 255, 0.8)"
            />
            <Panel position="bottom-center" className="bg-white p-2 rounded-t-lg border border-border">
              <div className="text-text-secondary text-sm">
                {nodes.length} nodes · {edges.length} connections
              </div>
            </Panel>
          </ReactFlow>
        </div>
      </div>
    </div>
  );
};

export default WorkflowEditor;