import apiClient from './client';

// Define the RunStatus enum matching the backend
export enum RunStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

// Define the structure of a Run based on the backend model
export interface Run {
  id: string; // UUID as string
  status: RunStatus;
  created_at: string; // Datetime as ISO string
  started_at: string | null; // Optional datetime as ISO string or null
  ended_at: string | null; // Optional datetime as ISO string or null
  runnable_id: string; // UUID as string
  runnable_type: 'agent' | 'team'; // Constrained string type
  input_variables: Record<string, any> | null; // Dict as Record or null
  output_data: Record<string, any> | null; // Dict as Record or null
}

// Interface for creating a run (matches RunCreate -> RunBase)
export interface RunCreateData {
  runnable_id: string;
  runnable_type: 'agent' | 'team';
  input_variables?: Record<string, any> | null;
}

// Function to fetch all runs (with optional filters)
export const fetchRuns = async (params?: { runnable_id?: string; status?: RunStatus; limit?: number; skip?: number }): Promise<Run[]> => {
  try {
    // Pass filters as query parameters
    const response = await apiClient.get<Run[]>('/runs', { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching runs:", error);
    throw error;
  }
};

// Function to fetch a single run by ID
export const fetchRunById = async (id: string): Promise<Run> => {
  try {
    const response = await apiClient.get<Run>(`/runs/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching run with ID ${id}:`, error);
    throw error;
  }
};

// Function to create/start a new run
export const createRun = async (runData: RunCreateData): Promise<Run> => {
  try {
    const response = await apiClient.post<Run>('/runs', runData);
    return response.data;
  } catch (error) {
    console.error("Error creating run:", error);
    throw error;
  }
};

// No update/delete endpoints currently defined in the backend for runs
