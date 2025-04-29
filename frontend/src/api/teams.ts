import apiClient from './client';

// Define the structure of a Team based on the backend model
export interface Team {
  id: string; // Changed from number to string
  name: string;
  description: string | null; // Added optional description
  agent_ids: string[]; // Added agent_ids (list of UUIDs as strings)
}

// Interface for creating a team (matches TeamCreate -> TeamBase)
export interface TeamCreateData {
  name: string;
  description?: string | null;
  agent_ids?: string[];
  // Note: member_ids are handled separately in backend endpoint, not part of TeamBase
}

// Interface for updating a team (matches TeamUpdate)
export interface TeamUpdateData {
  name?: string;
  description?: string | null; // Added from TeamBase as TeamUpdate inherits it
  agent_ids?: string[];
  // Note: member_ids are handled separately in backend endpoint
}

// Function to fetch all teams
export const fetchTeams = async (): Promise<Team[]> => {
  try {
    const response = await apiClient.get<Team[]>('/teams'); // Uses GET /api/v1/teams
    return response.data;
  } catch (error) {
    console.error("Error fetching teams:", error);
    throw error;
  }
};

// Function to fetch a single team by ID
export const fetchTeamById = async (id: string): Promise<Team> => {
  try {
    const response = await apiClient.get<Team>(`/teams/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching team with ID ${id}:`, error);
    throw error;
  }
};

// Function to create a new team
export const createTeam = async (teamData: TeamCreateData): Promise<Team> => {
  try {
    // The backend create_team expects TeamCreate which inherits TeamBase
    const response = await apiClient.post<Team>('/teams', teamData);
    return response.data;
  } catch (error) {
    console.error("Error creating team:", error);
    throw error;
  }
};

// Function to update an existing team
export const updateTeam = async (id: string, teamData: TeamUpdateData): Promise<Team> => {
  try {
    // The backend update_team expects TeamUpdate
    const response = await apiClient.put<Team>(`/teams/${id}`, teamData);
    return response.data;
  } catch (error) {
    console.error(`Error updating team with ID ${id}:`, error);
    throw error;
  }
};

// Function to delete a team
export const deleteTeam = async (id: string): Promise<void> => {
  try {
    await apiClient.delete(`/teams/${id}`);
  } catch (error) {
    console.error(`Error deleting team with ID ${id}:`, error);
    throw error;
  }
};
