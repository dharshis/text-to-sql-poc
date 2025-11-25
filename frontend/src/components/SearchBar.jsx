/**
 * SearchBar component - Query input interface.
 *
 * Allows users to select a client and enter a natural language query.
 */

import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  Typography,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

const SearchBar = ({ clients, onSubmit, loading }) => {
  const [selectedClient, setSelectedClient] = useState('');
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedClient && query.trim()) {
      onSubmit(query, selectedClient);
    }
  };

  const isSubmitDisabled = !selectedClient || !query.trim() || loading;

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
        Natural Language Query Interface
      </Typography>

      <Box component="form" onSubmit={handleSubmit}>
        {/* Client Selector */}
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel id="client-select-label">Select Client</InputLabel>
          <Select
            labelId="client-select-label"
            id="client-select"
            value={selectedClient}
            label="Select Client"
            onChange={(e) => setSelectedClient(e.target.value)}
            disabled={loading}
          >
            {clients.map((client) => (
              <MenuItem key={client.client_id} value={client.client_id}>
                {client.client_name} ({client.industry})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Query Input */}
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Enter your query"
          placeholder="e.g., Show me top 10 products by revenue in 2024"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
          sx={{ mb: 2 }}
          helperText="Ask questions about sales, products, revenue, or customer segments"
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

        {/* Selected Client Display */}
        {selectedClient && (
          <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
            Querying data for:{' '}
            <strong>
              {clients.find((c) => c.client_id === selectedClient)?.client_name}
            </strong>
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default SearchBar;
