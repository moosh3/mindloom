import { create } from 'zustand';
import { Node, Edge, Connection, addEdge, applyNodeChanges, applyEdgeChanges } from 'reactflow';

interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  workflowName: string;
  debugMode: boolean;
  isRunning: boolean;
  history: Array<{ nodes: Node[]; edges: Edge[] }>;
  historyIndex: number;
  tools: string[];
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: any) => void;
  onEdgesChange: (changes: any) => void;
  onConnect: (connection: Connection) => void;
  updateNodeData: (nodeId: string, data: any) => void;
  setSelectedNode: (node: Node | null) => void;
  setWorkflowName: (name: string) => void;
  setDebugMode: (enabled: boolean) => void;
  setIsRunning: (running: boolean) => void;
  addToHistory: () => void;
  undo: () => void;
  redo: () => void;
  addTool: (tool: string) => void;
  removeTool: (tool: string) => void;
}

const initialNodes: Node[] = [
  {
    id: 'start-1',
    type: 'start',
    position: { x: 100, y: 50 }, // Adjusted position
    data: { 
      triggerType: 'manual',
      label: 'Start',
    },
  },
];

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: initialNodes,
  edges: [],
  selectedNode: null,
  workflowName: 'Untitled Workflow',
  debugMode: false,
  isRunning: false,
  history: [{ nodes: initialNodes, edges: [] }],
  historyIndex: 0,
  tools: [],

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  onConnect: (connection) => {
    set((state) => ({
      edges: addEdge(connection, state.edges),
    }));
  },

  updateNodeData: (nodeId, data) => {
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
      ),
    }));
  },

  setSelectedNode: (node) => set({ selectedNode: node }),
  setWorkflowName: (name) => set({ workflowName: name }),
  setDebugMode: (enabled) => set({ debugMode: enabled }),
  setIsRunning: (running) => set({ isRunning: running }),

  addToHistory: () => {
    const { nodes, edges, history, historyIndex } = get();
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push({ nodes: [...nodes], edges: [...edges] });
    set({
      history: newHistory,
      historyIndex: historyIndex + 1,
    });
  },

  undo: () => {
    const { historyIndex, history } = get();
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      const { nodes, edges } = history[newIndex];
      set({
        nodes,
        edges,
        historyIndex: newIndex,
      });
    }
  },

  redo: () => {
    const { historyIndex, history } = get();
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      const { nodes, edges } = history[newIndex];
      set({
        nodes,
        edges,
        historyIndex: newIndex,
      });
    }
  },

  addTool: (tool) => set((state) => ({ tools: [...state.tools, tool] })),
  removeTool: (tool) =>
    set((state) => ({ tools: state.tools.filter((t) => t !== tool) })),
}));