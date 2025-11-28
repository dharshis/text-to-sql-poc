/**
 * SearchBar component - Query input interface.
 *
 * Allows users to enter a natural language query.
 * Client selection is now handled by the ClientSelector component.
 */

import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

const SearchBar = ({ clientId, onSubmit, loading, disabled }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (clientId && query.trim()) {
      onSubmit(query, clientId);
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift key)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSubmitDisabled) {
        handleSubmit(e);
      }
    }
  };

  const isSubmitDisabled = !clientId || !query.trim() || loading || disabled;

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
        Natural Language Query Interface
      </Typography>

      <Box component="form" onSubmit={handleSubmit}>
        {/* Query Input */}
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Enter your query"
          placeholder="e.g., Show me electric vehicle market trends from 2020 to 2023"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading || disabled}
          sx={{ mb: 2 }}
          helperText={
            disabled
              ? "Please select a client above to start querying"
              : "Ask questions about market size, trends, forecasts, or regional analysis"
          }
        />

        {/* Submit Button */}
        <Button
          type="submit"
          variant="contained"
          size="large"
          fullWidth
          disabled={isSubmitDisabled}
          startIcon={<SearchIcon />}
          sx={{ height: 48 }}
        >
          {loading ? 'Processing...' : 'Search'}
        </Button>
      </Box>
    </Paper>
  );
};

export default SearchBar;
