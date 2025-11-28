/**
 * ClientSelector Component
 *
 * Displays a dropdown to select the active client for querying.
 * Shows only the client name in the dropdown.
 */

import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  CircularProgress
} from '@mui/material';

const ClientSelector = ({ clients, selectedClientId, onClientChange, loading }) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 250 }}>
        <CircularProgress size={20} />
        <Typography variant="body2">Loading clients...</Typography>
      </Box>
    );
  }

  if (!clients || clients.length === 0) {
    return (
      <Box sx={{ p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
        <Typography variant="body2">No clients available</Typography>
      </Box>
    );
  }

  return (
    <FormControl fullWidth size="small" sx={{ minWidth: 300 }}>
      <InputLabel id="client-select-label">Select Client</InputLabel>
      <Select
        labelId="client-select-label"
        id="client-select"
        value={selectedClientId || ''}
        label="Select Client"
        onChange={(e) => onClientChange(e.target.value)}
        sx={{ bgcolor: 'background.paper' }}
      >
        {clients.map((client) => (
          <MenuItem key={client.client_id} value={client.client_id}>
            {client.client_name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default ClientSelector;


