/**
 * API client service for Text-to-SQL POC frontend.
 *
 * Provides functions to interact with the Flask backend API.
 */

import axios from 'axios';

// Base URL for API - matches backend Flask server
const API_BASE_URL = 'http://localhost:5001';

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

export default {
  fetchClients,
  submitQuery,
  checkHealth,
  fetchSchema,
};
