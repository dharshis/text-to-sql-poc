/**
 * ChatInput Component
 *
 * Modern chat input with send button and keyboard shortcuts
 */

import React, { useState } from 'react';
import { Box, TextField, IconButton, InputAdornment, Paper } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const ChatInput = ({ onSubmit, disabled, loading, value, onChange }) => {
  const [internalQuery, setInternalQuery] = useState('');

  // Use controlled value if provided, otherwise use internal state
  const query = value !== undefined ? value : internalQuery;
  const setQuery = onChange || setInternalQuery;

  const handleSubmit = () => {
    if (query.trim() && !disabled && !loading) {
      onSubmit(query.trim());
      // Only clear if using internal state
      if (value === undefined) {
        setQuery('');
      }
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        borderTop: '1px solid',
        borderColor: 'divider',
        backgroundColor: 'background.paper',
      }}
    >
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your data..."
          disabled={disabled || loading}
          variant="outlined"
          sx={{
            '& .MuiOutlinedInput-root': {
              paddingRight: 0,
            },
          }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={handleSubmit}
                  disabled={!query.trim() || disabled || loading}
                  color="primary"
                  sx={{
                    mr: -0.5,
                    '&:hover': {
                      backgroundColor: 'primary.main',
                      color: 'white',
                    },
                  }}
                >
                  <SendIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Box>
      <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box
          component="span"
          sx={{
            fontSize: '0.75rem',
            color: 'text.secondary',
          }}
        >
          Press <kbd style={{ padding: '2px 6px', backgroundColor: '#f3f4f6', borderRadius: '4px', fontSize: '0.7rem' }}>Enter</kbd> to send, <kbd style={{ padding: '2px 6px', backgroundColor: '#f3f4f6', borderRadius: '4px', fontSize: '0.7rem' }}>Shift+Enter</kbd> for new line
        </Box>
        {query.length > 0 && (
          <Box
            component="span"
            sx={{
              fontSize: '0.75rem',
              color: query.length > 500 ? 'error.main' : 'text.secondary',
            }}
          >
            {query.length} / 1000
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default ChatInput;
