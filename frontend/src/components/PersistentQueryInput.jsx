/**
 * PersistentQueryInput Component
 *
 * Fixed bottom input bar for submitting queries.
 * Features:
 * - Multiline text input
 * - Submit button with loading state
 * - Keyboard handling (Enter to submit, Shift+Enter for new line)
 * - Disabled when no client selected
 */

import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';

const PersistentQueryInput = ({ clientId, onSubmit, loading, disabled }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (clientId && query.trim()) {
      onSubmit(query, clientId);
      setQuery(''); // Clear input after submission
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
    <Paper
      elevation={8}
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        backgroundColor: 'background.paper',
        borderTop: '1px solid',
        borderColor: 'divider',
        p: 2,
      }}
    >
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          gap: 2,
          alignItems: 'flex-end',
        }}
      >
        {/* Query Input */}
        <TextField
          fullWidth
          multiline
          maxRows={3}
          placeholder={
            disabled || !clientId
              ? "Select a client to start querying..."
              : "Ask a question about market trends, forecasts, or analysis..."
          }
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading || disabled || !clientId}
          variant="outlined"
          sx={{
            '& .MuiOutlinedInput-root': {
              backgroundColor: 'background.default',
            },
          }}
        />

        {/* Submit Button */}
        <Button
          type="submit"
          variant="contained"
          size="large"
          disabled={isSubmitDisabled}
          endIcon={<SendIcon />}
          sx={{
            minWidth: 120,
            height: 56,
            fontWeight: 600,
          }}
        >
          {loading ? 'Processing...' : 'Send'}
        </Button>
      </Box>
    </Paper>
  );
};

export default PersistentQueryInput;
