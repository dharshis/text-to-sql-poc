/**
 * ContextBadge Component
 * Architecture Reference: Section 9.2 (Component Specifications)
 * Story 7.3 - AC7: Enhanced with clear button
 * 
 * Displays context for follow-up queries with option to clear conversation.
 */

import React from 'react';
import { Chip } from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';

const ContextBadge = ({ previousQuery, isFollowup, onClear }) => {
  if (!isFollowup || !previousQuery) {
    return null;
  }

  return (
    <Chip
      icon={<HistoryIcon />}
      label={`Following up on: ${previousQuery.substring(0, 50)}${previousQuery.length > 50 ? '...' : ''}`}
      onDelete={onClear} // Shows [×] button when provided
      color="info"
      variant="outlined"
      sx={{ mb: 2, maxWidth: '100%' }}
    />
  );
};

export default ContextBadge;

