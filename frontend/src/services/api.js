/**
 * API client service for Text-to-SQL POC frontend.
 *
 * Provides functions to interact with the Flask backend API.
 */

import axios from 'axios';

// Base URL for API - matches backend Flask server
const API_BASE_URL = 'http://localhost:5000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Fetch list of available clients from the backend.
 *
 * @returns {Promise<Array>} Array of client objects
 * @throws {Error} If API call fails
 */
export const fetchClients = async () => {
  try {
    const response = await apiClient.get('/clients');
    return response.data.clients;
  } catch (error) {
    console.error('Error fetching clients:', error);
    throw new Error(
      error.response?.data?.error ||
      'Failed to fetch clients. Please check if the backend server is running.'
    );
  }
};

/**
 * Submit a natural language query to the backend.
 *
 * @param {string} query - Natural language query
 * @param {number} clientId - Client ID for data filtering
 * @returns {Promise<Object>} Query results with SQL, data, validation, and metrics
 * @throws {Error} If API call fails
 */
export const submitQuery = async (query, clientId) => {
  try {
    const response = await apiClient.post('/query', {
      query,
      client_id: clientId,
    });
    return response.data;
  } catch (error) {
    console.error('Error submitting query:', error);

    // Extract error message from response
    const errorMessage = error.response?.data?.error ||
                        error.response?.data?.message ||
                        'Query failed. Please try again.';

    const errorDetails = error.response?.data?.details || '';

    // Return error data if available (for validation failures)
    if (error.response?.data) {
      throw {
        message: errorMessage,
        details: errorDetails,
        data: error.response.data,
        isValidationError: error.response.status === 400
      };
    }

    throw new Error(errorMessage);
  }
};

/**
 * Check backend health status.
 *
 * @returns {Promise<Object>} Health status object
 * @throws {Error} If API call fails
 */
export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('Error checking health:', error);
    throw new Error('Backend server is not responding.');
  }
};

/**
 * Get database schema information.
 *
 * @returns {Promise<string>} Database schema
 * @throws {Error} If API call fails
 */
export const fetchSchema = async () => {
  try {
    const response = await apiClient.get('/schema');
    return response.data.schema;
  } catch (error) {
    console.error('Error fetching schema:', error);
    throw new Error('Failed to fetch database schema.');
  }
};

/**
 * Submit a natural language query to the agentic endpoint.
 * Architecture Reference: Section 9.3 (Frontend State Management)
 * 
 * @param {string} query - Natural language query
 * @param {string} sessionId - Session ID for conversation context
 * @param {number} clientId - Client ID for data filtering
 * @param {number} maxIterations - Maximum iterations for agent workflow
 * @returns {Promise<Object>} Agentic query results with explanation, reflection, etc.
 * @throws {Error} If API call fails
 */
export const executeAgenticQuery = async (query, sessionId, clientId = 1, maxIterations = 10) => {
  try {
    const response = await apiClient.post('/query-agentic', {
      query,
      session_id: sessionId,
      client_id: clientId,
      max_iterations: maxIterations,
    });
    return response.data;
  } catch (error) {
    console.error('Error executing agentic query:', error);

    // Extract error message from response
    const errorMessage = error.response?.data?.error ||
                        error.response?.data?.message ||
                        'Agentic query failed. Please try again.';

    const errorDetails = error.response?.data?.details || '';

    // Return error data if available
    if (error.response?.data) {
      throw {
        message: errorMessage,
        details: errorDetails,
        data: error.response.data,
        isApiError: true
      };
    }

    throw new Error(errorMessage);
  }
};

/**
 * Delete a session and all its conversation history from backend.
 * Session Memory Feature: Ensures complete cleanup when starting new session.
 * 
 * @param {string} sessionId - Session ID to delete
 * @returns {Promise<Object>} Deletion confirmation
 * @throws {Error} If API call fails
 */
export const deleteSession = async (sessionId) => {
  try {
    const response = await apiClient.delete(`/session/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting session:', error);
    // Don't throw - session might not exist, that's okay
    return { success: false, error: error.message };
  }
};

export default {
  fetchClients,
  submitQuery,
  checkHealth,
  fetchSchema,
  executeAgenticQuery,
  deleteSession,
};
