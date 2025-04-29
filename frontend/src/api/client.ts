// Proposed content for /Users/aleccunningham/Projects/github.com/moosh3/agentui/frontend/src/api/client.ts

import axios from 'axios';

// Retrieve the base URL from environment variables
const baseURL = import.meta.env.VITE_API_BASE_URL;

if (!baseURL) {
  console.error("VITE_API_BASE_URL is not defined. Please check your .env file.");
}

// Create an axios instance with default configuration
const apiClient = axios.create({
  baseURL: baseURL || '/api/v1', // Fallback just in case, relies on proxy
  headers: {
    'Content-Type': 'application/json',
    // Add other default headers if needed, e.g., Authorization
  },
});

// Optional: Add request/response interceptors here if needed
// apiClient.interceptors.request.use(...)
// apiClient.interceptors.response.use(...)

export default apiClient;
