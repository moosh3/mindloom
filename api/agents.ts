import apiClient from './client';

// Define the structure of an Agent based on the backend Agent Pydantic model
export interface Agent {
  id: string; // Changed from number to string to match UUID
  name: string;
  description: string | null; // Allow null for optional description
  model_provider: string;
  model_name: string;
  temperature: number; // Changed from float to number
  tools: string[]; // Changed from List[str] to string[]
}

// Interface for creating an agent (matches AgentBase in backend)
export interface AgentCreateData {
  name: string;
  description?: string | null;
  model_provider: string;
  model_name: string;
  temperature?: number;
  tools?: string[];
}

// Interface for updating an agent (matches AgentUpdate in backend)
export type AgentUpdateData = Partial<AgentCreateData>; // All fields are optional

// Function to fetch all agents
export const fetchAgents = async (): Promise<Agent[]> => {
  try {
    const response = await apiClient.get<Agent[]>('/agents'); // Uses GET /api/v1/agents
    return response.data;
  } catch (error) {
    console.error("Error fetching agents:", error);
    // You might want to throw the error or return a default value
    throw error; // Re-throw the error to be handled by the caller
  }
};

// Function to fetch a single agent by ID
export const fetchAgentById = async (id: string): Promise<Agent> => {
  try {
    const response = await apiClient.get<Agent>(`/agents/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching agent with ID ${id}:`, error);
    throw error;
  }
};

// Function to create a new agent
export const createAgent = async (agentData: AgentCreateData): Promise<Agent> => {
  try {
    const response = await apiClient.post<Agent>('/agents', agentData);
    return response.data;
  } catch (error) {
    console.error("Error creating agent:", error);
    throw error;
  }
};

// Function to update an existing agent
export const updateAgent = async (id: string, agentData: AgentUpdateData): Promise<Agent> => {
  try {
    const response = await apiClient.put<Agent>(`/agents/${id}`, agentData);
    return response.data;
  } catch (error) {
    console.error(`Error updating agent with ID ${id}:`, error);
    throw error;
  }
};

// Function to delete an agent
export const deleteAgent = async (id: string): Promise<void> => {
  try {
    await apiClient.delete(`/agents/${id}`);
  } catch (error) {
    console.error(`Error deleting agent with ID ${id}:`, error);
    throw error;
  }
};
