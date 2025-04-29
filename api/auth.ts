import apiClient from './client';

// Interface for User object (returned from API, excluding password)
export interface User {
  id: string; // UUID
  email: string;
  full_name: string | null;
  department: string | null;
  is_active: boolean;
  is_superuser: boolean;
  role: string;
  created_at: string; // ISO Date string
  updated_at: string | null; // ISO Date string or null
}

// Interface for User creation data (matches UserCreate)
export interface UserCreateData {
  email: string;
  password: string;
  full_name?: string | null;
  department?: string | null;
  // is_active, is_superuser, role have defaults in backend
}

// Interface for Token object (returned from login/refresh)
export interface Token {
  access_token: string;
  token_type: string;
  refresh_token?: string | null;
}

// Interface for Refresh Token Request body
export interface RefreshTokenRequestData {
  refresh_token: string;
}

// Function to register a new user
export const register = async (userData: UserCreateData): Promise<User> => {
  try {
    const response = await apiClient.post<User>('/auth/register', userData);
    return response.data;
  } catch (error) {
    console.error("Error registering user:", error);
    throw error;
  }
};

// Function to log in a user
// Uses FormData to match OAuth2PasswordRequestForm expectation
export const login = async (email: string, password: string): Promise<Token> => {
  try {
    const formData = new FormData();
    formData.append('username', email); // Backend expects 'username'
    formData.append('password', password);

    const response = await apiClient.post<Token>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded', // Important for FormData
      },
    });
    // TODO: Store tokens securely (e.g., localStorage, state management)
    return response.data;
  } catch (error) {
    console.error("Error logging in:", error);
    throw error;
  }
};

// Function to refresh the access token
export const refreshToken = async (refreshTokenData: RefreshTokenRequestData): Promise<Token> => {
  try {
    const response = await apiClient.post<Token>('/auth/refresh', refreshTokenData);
    // TODO: Update stored access token
    return response.data;
  } catch (error) {
    console.error("Error refreshing token:", error);
    // TODO: Handle refresh failure (e.g., redirect to login)
    throw error;
  }
};

// Function to fetch the current user's details
export const fetchCurrentUser = async (): Promise<User> => {
  try {
    // Assumes the access token is automatically included by apiClient interceptors
    const response = await apiClient.get<User>('/auth/users/me');
    return response.data;
  } catch (error) {
    console.error("Error fetching current user:", error);
    // TODO: Handle auth error (e.g., redirect to login)
    throw error;
  }
};

// Potential Logout function
// export const logout = async (): Promise<void> => {
//   // TODO: Clear stored tokens
//   // TODO: Potentially notify backend (if invalidate endpoint exists)
//   console.log('User logged out');
// };
