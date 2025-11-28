/**
 * ResultsDisplay component - Container for query results.
 *
 * Organizes and displays all result components:
 * - Loading state
 * - Error state
 * - Data visualization
 * - Data table
 * - SQL display
 * - Validation metrics
 */

import React from 'react';
import { Box, CircularProgress, Alert, Typography } from '@mui/material';
import DataVisualization from './DataVisualization';
import DataTable from './DataTable';
import SqlDisplay from './SqlDisplay';
import ValidationSummary from './ValidationSummary';

const ResultsDisplay = ({ loading, error, results, reflection }) => {
  // Loading state
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 300,
          gap: 2,
        }}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="text.secondary">
          Processing your query...
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Generating SQL and executing query
        </Typography>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          {error.message || 'An error occurred'}
        </Typography>
        {error.details && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            {error.details}
          </Typography>
        )}

        {/* Show validation errors if available */}
        {error.data?.validation && (
          <Box sx={{ mt: 2 }}>
            <ValidationMetrics validation={error.data.validation} />
          </Box>
        )}

        {/* Show SQL if available */}
        {error.data?.sql && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Generated SQL:
            </Typography>
            <Box
              sx={{
                p: 1,
                backgroundColor: 'grey.100',
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                overflow: 'auto',
              }}
            >
              {error.data.sql}
            </Box>
          </Box>
        )}
      </Alert>
    );
  }

  // No results yet
  if (!results) {
    return (
      <Box
        sx={{
          textAlign: 'center',
          py: 8,
          color: 'text.secondary',
        }}
      >
        <Typography variant="h6" gutterBottom>
          No results yet
        </Typography>
        <Typography variant="body2">
          Select a client and enter a query to get started
        </Typography>
      </Box>
    );
  }

  // Display results
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, width: '100%', maxWidth: '100%' }}>
      {/* Performance Metrics */}
      {results.metrics && (
        <Alert severity="info" icon={false} sx={{ width: '100%', boxSizing: 'border-box' }}>
          <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
            <strong>Performance:</strong> Total time {results.metrics.total_time}s
            {' | '}
            SQL generation: {results.metrics.sql_generation_time}s
            {' | '}
            Validation: {results.metrics.validation_time}s
            {' | '}
            Execution: {results.metrics.query_execution_time}s
            {' | '}
            Results: {results.row_count} rows
          </Typography>
        </Alert>
      )}

      {/* Data Visualization */}
      {results.results && results.results.length > 0 && (
        <DataVisualization data={results.results} columns={results.columns} />
      )}

      {/* Data Table */}
      {results.results && results.results.length > 0 && (
        <DataTable data={results.results} columns={results.columns} />
      )}

      {/* SQL Display */}
      {results.sql && <SqlDisplay sql={results.sql} />}

      {/* Unified Validation Summary - Quality Check + Security Validation */}
      {(reflection || results.validation) && (
        <ValidationSummary
          reflection={reflection}
          securityValidation={results.validation}
        />
      )}
    </Box>
  );
};

export default ResultsDisplay;
