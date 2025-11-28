/**
 * SqlDisplay component - Generated SQL query display.
 *
 * Shows the generated SQL with syntax highlighting and copy functionality.
 */

import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  IconButton,
  Collapse,
  Tooltip,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

const SqlDisplay = ({ sql }) => {
  const [expanded, setExpanded] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopySuccess(true);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleClose = () => {
    setCopySuccess(false);
  };

  // Simple SQL syntax highlighting
  const highlightSQL = (query) => {
    if (!query) return '';

    const keywords = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|HAVING|AS|AND|OR|IN|NOT|NULL|LIMIT|DISTINCT|COUNT|SUM|AVG|MAX|MIN)\b/gi;
    const strings = /('(?:[^'\\]|\\.)*')/g;
    const numbers = /\b(\d+\.?\d*)\b/g;

    let highlighted = query;

    // Replace keywords
    highlighted = highlighted.replace(keywords, '<span style="color: #1976d2; font-weight: bold">$1</span>');

    // Replace strings
    highlighted = highlighted.replace(strings, '<span style="color: #4caf50">$1</span>');

    // Replace numbers
    highlighted = highlighted.replace(numbers, '<span style="color: #ff9800">$1</span>');

    return highlighted;
  };

  if (!sql) {
    return null;
  }

  return (
    <>
      <Paper sx={{ p: 2, width: '100%', maxWidth: '100%', overflow: 'hidden', boxSizing: 'border-box' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CodeIcon color="primary" />
            <Typography variant="h6">Generated SQL Query</Typography>
          </Box>

          <Box sx={{ display: 'flex' }}>
            <Tooltip title="Copy SQL">
              <IconButton onClick={handleCopy} size="small">
                <CopyIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={expanded ? 'Collapse' : 'Expand'}>
              <IconButton
                onClick={() => setExpanded(!expanded)}
                size="small"
                sx={{
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s',
                }}
              >
                <ExpandMoreIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Collapse in={expanded} timeout="auto">
          <Box
            sx={{
              mt: 2,
              p: 2,
              backgroundColor: 'grey.100',
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              lineHeight: 1.6,
              overflowX: 'auto',
              overflowY: 'auto',
              maxHeight: 300,
              wordBreak: 'break-word',
            }}
            dangerouslySetInnerHTML={{ __html: highlightSQL(sql) }}
          />
        </Collapse>

        {!expanded && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mt: 1,
              fontFamily: 'monospace',
              fontSize: '0.75rem',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {sql}
          </Typography>
        )}
      </Paper>

      {/* Copy success notification */}
      <Snackbar
        open={copySuccess}
        autoHideDuration={2000}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleClose} severity="success" variant="filled">
          SQL copied to clipboard!
        </Alert>
      </Snackbar>
    </>
  );
};

export default SqlDisplay;
