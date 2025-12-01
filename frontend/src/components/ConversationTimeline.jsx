/**
 * ConversationTimeline Component
 *
 * Container for all timeline cards.
 * Responsibilities:
 * - Render TimelineCard for each conversation entry
 * - Auto-scroll to latest query
 * - Show empty state when no queries
 * - Handle loading and error states
 * - Manage expansion logic (only one historical card expanded at a time)
 */

import React, { useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import TimelineCard from './TimelineCard';

const ConversationTimeline = ({
  conversationHistory,
  currentResults,
  currentAgenticData,
  currentQueryIndex,
  expandedHistoryIndex,
  onCardExpand,
  loading,
  error,
}) => {
  const timelineEndRef = useRef(null);

  // Auto-scroll to latest query
  useEffect(() => {
    if (currentQueryIndex >= 0) {
      timelineEndRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'end',
      });
    }
  }, [currentQueryIndex]);

  // Empty state - no queries yet
  if (conversationHistory.length === 0 && !loading && !error) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          gap: 3,
          px: 3,
        }}
      >
        <Typography
          variant="h5"
          color="text.secondary"
          sx={{ fontWeight: 600, textAlign: 'center' }}
        >
          Welcome to Smart Insight Generator
        </Typography>

        <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center' }}>
          Select a client and ask your first question below
        </Typography>

        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontWeight: 600 }}>
            Try asking:
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'center' }}>
            <Chip
              label="Show me electric vehicle market trends from 2020 to 2023"
              sx={{ maxWidth: '100%' }}
            />
            <Chip
              label="What are the top performing categories in Europe?"
              sx={{ maxWidth: '100%' }}
            />
            <Chip
              label="Compare market sizes across Asia-Pacific regions"
              sx={{ maxWidth: '100%' }}
            />
          </Box>
        </Box>
      </Box>
    );
  }

  // Loading state (for first query)
  if (loading && conversationHistory.length === 0) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
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

  // Error state (when no history and error occurs)
  if (error && conversationHistory.length === 0) {
    return (
      <Box sx={{ maxWidth: 1200, margin: '0 auto', p: 3 }}>
        <Alert severity="error">
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {error.message || 'An error occurred'}
          </Typography>
          {error.details && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              {error.details}
            </Typography>
          )}
        </Alert>
      </Box>
    );
  }

  // Render timeline cards
  return (
    <Box
      sx={{
        maxWidth: 1200,
        margin: '0 auto',
        p: 3,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {conversationHistory.map((entry, index) => {
        const isCurrent = index === currentQueryIndex;
        const isExpanded = index === expandedHistoryIndex;

        // Get results for this card
        const cardResults = isCurrent ? currentResults : entry.fullResults?.results;
        const cardAgenticData = isCurrent ? currentAgenticData : entry.fullResults?.agenticData;

        return (
          <TimelineCard
            key={`${entry.timestamp}-${index}`}
            entry={entry}
            results={cardResults}
            agenticData={cardAgenticData}
            isExpanded={isExpanded}
            isCurrent={isCurrent}
            onExpand={() => onCardExpand(index)}
            onCollapse={() => onCardExpand(-1)}
          />
        );
      })}

      {/* Loading indicator for subsequent queries */}
      {loading && conversationHistory.length > 0 && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            p: 3,
            border: '2px dashed',
            borderColor: 'primary.main',
            borderRadius: 2,
            bgcolor: 'action.hover',
          }}
        >
          <CircularProgress size={40} />
          <Box>
            <Typography variant="h6" color="text.secondary">
              Processing your query...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Generating SQL and executing query
            </Typography>
          </Box>
        </Box>
      )}

      {/* Error indicator for subsequent queries */}
      {error && conversationHistory.length > 0 && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {error.message || 'An error occurred'}
          </Typography>
          {error.details && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              {error.details}
            </Typography>
          )}
        </Alert>
      )}

      {/* Scroll anchor */}
      <div ref={timelineEndRef} />
    </Box>
  );
};

export default ConversationTimeline;
