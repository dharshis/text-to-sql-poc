/**
 * App - Main application component
 *
 * Orchestrates the text-to-SQL POC interface:
 * - Fetches clients on mount
 * - Handles query submission
 * - Manages loading/error states
 * - Displays results
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Alert,
  ThemeProvider,
  CssBaseline,
  Chip,
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import theme from './styles/theme';
import SearchBar from './components/SearchBar';
import ResultsDisplay from './components/ResultsDisplay';
import { fetchClients, submitQuery, checkHealth } from './services/api';

function App() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);

  // Fetch clients on mount
  useEffect(() => {
    const loadClients = async () => {
      try {
        const clientList = await fetchClients();
        setClients(clientList);
      } catch (err) {
        console.error('Failed to fetch clients:', err);
        setError({
          message: 'Failed to load clients',
          details: err.message || 'Could not connect to backend',
        });
      }
    };

    const checkBackendHealth = async () => {
      try {
        const health = await checkHealth();
        setHealthStatus(health);
      } catch (err) {
        console.error('Backend health check failed:', err);
        setHealthStatus({ status: 'unhealthy', error: err.message });
      }
    };

    loadClients();
    checkBackendHealth();
  }, []);

  // Handle query submission
  const handleQuerySubmit = async (query, clientId) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await submitQuery(query, clientId);
      setResults(data);
    } catch (err) {
      console.error('Query failed:', err);

      // Extract error details from response
      let errorMessage = 'Failed to process query';
      let errorDetails = err.message;
      let errorData = null;

      if (err.response?.data) {
        errorMessage = err.response.data.error || errorMessage;
        errorDetails = err.response.data.message || errorDetails;
        errorData = {
          sql: err.response.data.sql,
          validation: err.response.data.validation,
        };
      }

      setError({
        message: errorMessage,
        details: errorDetails,
        data: errorData,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="h3" component="h1" sx={{ fontWeight: 600 }}>
              Text-to-SQL Query Tool
            </Typography>

            {/* Backend Health Status */}
            {healthStatus && (
              <Chip
                icon={healthStatus.status === 'healthy' ? <CheckCircle /> : <ErrorIcon />}
                label={`Backend: ${healthStatus.status || 'Unknown'}`}
                color={healthStatus.status === 'healthy' ? 'success' : 'error'}
                variant="outlined"
              />
            )}
          </Box>

          <Typography variant="body1" color="text.secondary">
            Ask questions in natural language, get SQL results with visualizations
          </Typography>
        </Box>

        {/* Backend Connection Error */}
        {!healthStatus || healthStatus.status !== 'healthy' && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="subtitle2">
              Backend connection issue
            </Typography>
            <Typography variant="body2">
              Make sure the backend server is running on http://localhost:5001
            </Typography>
          </Alert>
        )}

        {/* Search Bar */}
        <Box sx={{ mb: 4 }}>
          <SearchBar
            clients={clients}
            onSubmit={handleQuerySubmit}
            loading={loading}
          />
        </Box>

        {/* Results Display */}
        <ResultsDisplay
          loading={loading}
          error={error}
          results={results}
        />
      </Container>
    </ThemeProvider>
  );
}

export default App;
