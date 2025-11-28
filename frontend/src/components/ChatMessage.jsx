/**
 * ChatMessage Component
 *
 * Renders user queries and AI responses in a chat-like interface.
 * User messages: Simple bubble on the right
 * AI messages: Comprehensive response on the left with all result components
 */

import React, { useEffect, useRef, useState } from 'react';
import { Box, Paper, Typography, Avatar, Chip, Alert } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { formatDistanceToNow } from 'date-fns';

// Import result components
import InsightCard from './InsightCard';
import DataVisualization from './DataVisualization';
import DataTable from './DataTable';
import SqlDisplay from './SqlDisplay';
import ValidationSummary from './ValidationSummary';

const ChatMessage = ({ message, isUser, isLatest, onSuggestedQuestionClick }) => {
  const timestamp = message.timestamp ? new Date(message.timestamp) : new Date();
  const timeAgo = formatDistanceToNow(timestamp, { addSuffix: true });
  const messageRef = useRef(null);
  const [highlight, setHighlight] = useState(false);

  // Generate suggested follow-up questions based on the response
  const generateSuggestedQuestions = () => {
    if (isUser || !message.results || message.results.length === 0) return [];

    const suggestions = [];

    // Based on data presence
    if (message.results && message.results.length > 0) {
      suggestions.push('Show me the trends over time');
      suggestions.push('What are the key insights from this data?');
    }

    // Based on columns
    if (message.columns && message.columns.length > 0) {
      const hasDateColumn = message.columns.some(col =>
        /date|time|month|year|quarter/i.test(col)
      );
      const hasValueColumn = message.columns.some(col =>
        /revenue|sales|amount|value|total|price/i.test(col)
      );

      if (hasDateColumn && hasValueColumn) {
        suggestions.push('Compare this with previous period');
      }

      if (message.columns.length > 2) {
        suggestions.push('Break this down by category');
      }
    }

    // Generic suggestions
    suggestions.push('Can you visualize this differently?');
    suggestions.push('What caused these results?');

    // Return up to 4 suggestions
    return suggestions.slice(0, 4);
  };

  const suggestedQuestions = !isUser ? generateSuggestedQuestions() : [];

  // Auto-scroll and highlight for latest AI message
  useEffect(() => {
    if (!isUser && isLatest && messageRef.current) {
      // Scroll to the message
      messageRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // Trigger highlight
      setHighlight(true);

      // Remove highlight after 3 seconds
      const timer = setTimeout(() => {
        setHighlight(false);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [isUser, isLatest]);

  if (isUser) {
    // User message - simple bubble on the right
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'flex-end',
          mb: 3,
          alignItems: 'flex-start',
          gap: 2,
          maxWidth: '100%',
        }}
      >
        <Box sx={{ maxWidth: '70%', textAlign: 'right', minWidth: 0 }}>
          <Paper
            elevation={1}
            sx={{
              px: 3,
              py: 2,
              background: 'linear-gradient(135deg, #34657F 0%, #00AED9 100%)',
              color: 'white',
              borderRadius: '18px 18px 4px 18px',
              display: 'inline-block',
              textAlign: 'left',
              maxWidth: '100%',
              boxSizing: 'border-box',
              wordBreak: 'break-word',
            }}
          >
            <Typography variant="body1" sx={{ wordBreak: 'break-word' }}>
              {message.query}
            </Typography>
          </Paper>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: 'block', mt: 0.5, mr: 1 }}
          >
            {timeAgo}
          </Typography>
        </Box>
        <Avatar
          sx={{
            bgcolor: 'primary.main',
            width: 36,
            height: 36,
            flexShrink: 0,
          }}
        >
          <PersonIcon fontSize="small" />
        </Avatar>
      </Box>
    );
  }

  // AI message - comprehensive response on the left
  return (
    <Box
      ref={messageRef}
      sx={{
        display: 'flex',
        justifyContent: 'flex-start',
        mb: 4,
        alignItems: 'flex-start',
        gap: 2,
        maxWidth: '100%',
      }}
    >
      <Avatar
        sx={{
          bgcolor: message.error ? 'error.main' : 'success.main',
          width: 36,
          height: 36,
          flexShrink: 0,
        }}
      >
        <SmartToyIcon fontSize="small" />
      </Avatar>
      <Box sx={{ maxWidth: '85%', flex: 1, minWidth: 0 }}>
        {/* AI Response Container */}
        <Paper
          elevation={2}
          sx={{
            p: 3,
            borderRadius: '18px 18px 18px 4px',
            border: '2px solid',
            borderColor: highlight
              ? 'primary.main'
              : message.error
                ? 'error.light'
                : 'divider',
            backgroundColor: highlight
              ? 'rgba(25, 118, 210, 0.04)'
              : 'background.paper',
            maxWidth: '100%',
            boxSizing: 'border-box',
            overflow: 'hidden',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          {/* Error Display */}
          {message.error && (
            <Box sx={{ mb: message.sql || message.validation ? 3 : 0 }}>
              <Alert severity="error" sx={{ borderRadius: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                  {message.error}
                </Typography>
                {message.errorDetails && (
                  <Typography variant="body2" color="text.secondary">
                    {message.errorDetails}
                  </Typography>
                )}
              </Alert>
            </Box>
          )}

          {/* Status indicator */}
          {message.isFollowup && (
            <Chip
              label="Follow-up Query"
              size="small"
              color="info"
              variant="outlined"
              sx={{ mb: 2 }}
            />
          )}

          {/* Insight Card */}
          {message.explanation && (
            <Box sx={{ mb: 3 }}>
              <InsightCard explanation={message.explanation} />
            </Box>
          )}

          {/* Data Visualization */}
          {message.results && message.results.length > 0 && message.columns && (
            <Box sx={{ mb: 3 }}>
              <DataVisualization
                data={message.results}
                columns={message.columns}
              />
            </Box>
          )}

          {/* Data Table */}
          {message.results && message.results.length > 0 && message.columns && (
            <Box sx={{ mb: 3 }}>
              <DataTable data={message.results} columns={message.columns} />
            </Box>
          )}

          {/* SQL Display */}
          {message.sql && (
            <Box sx={{ mb: 3 }}>
              <SqlDisplay sql={message.sql} />
            </Box>
          )}

          {/* Validation Summary */}
          {(message.reflection || message.validation) && (
            <Box>
              <ValidationSummary
                reflection={message.reflection}
                securityValidation={message.validation}
              />
            </Box>
          )}

          {/* Empty state - no results */}
          {!message.error &&
            !message.explanation &&
            (!message.results || message.results.length === 0) &&
            !message.sql && (
              <Box sx={{ py: 4, textAlign: 'center' }}>
                <Typography variant="body1" color="text.secondary">
                  No results found for this query.
                </Typography>
              </Box>
            )}

          {/* Suggested Questions */}
          {suggestedQuestions.length > 0 && (
            <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="subtitle2" sx={{ mb: 1.5, color: 'text.secondary', fontWeight: 500 }}>
                💡 Suggested follow-up questions:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {suggestedQuestions.map((question, index) => (
                  <Chip
                    key={index}
                    label={question}
                    onClick={() => onSuggestedQuestionClick && onSuggestedQuestionClick(question)}
                    variant="outlined"
                    sx={{
                      borderColor: 'primary.main',
                      color: 'primary.main',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      '&.MuiChip-clickable:hover': {
                        backgroundColor: 'primary.main',
                        borderColor: 'primary.main',
                        color: 'white',
                        transform: 'translateY(-2px)',
                        boxShadow: 2,
                      },
                      '&:hover': {
                        backgroundColor: 'primary.main',
                        borderColor: 'primary.main',
                        color: 'white',
                        transform: 'translateY(-2px)',
                        boxShadow: 2,
                      },
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}
        </Paper>

        {/* Timestamp */}
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mt: 0.5, ml: 1 }}
        >
          {timeAgo}
        </Typography>
      </Box>
    </Box>
  );
};

export default ChatMessage;
