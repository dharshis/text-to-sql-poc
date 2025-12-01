/**
 * TimelineCard Component
 *
 * Individual conversation entry in the timeline.
 * Two display states:
 * - Collapsed: Question + metadata + timestamp (clickable to expand)
 * - Expanded/Current: Full results with all components
 *
 * Features:
 * - Follow-up indicators (left border + indentation)
 * - Hover effects on collapsed cards
 * - Success/error status badges
 * - Current query highlighting
 */

import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  SubdirectoryArrowRight as SubdirectoryArrowRightIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import InsightCard from './InsightCard';
import DataVisualization from './DataVisualization';
import DataTable from './DataTable';
import SqlDisplay from './SqlDisplay';
import ValidationSummary from './ValidationSummary';
import ContextBadge from './ContextBadge';

const TimelineCard = React.memo(({
  entry,
  results,
  agenticData,
  isExpanded,
  isCurrent,
  onExpand,
  onCollapse,
}) => {
  // Collapsed state for historical queries
  if (!isExpanded && !isCurrent) {
    return (
      <Card
        onClick={onExpand}
        sx={{
          cursor: 'pointer',
          borderLeft: entry.is_followup ? '4px solid' : 'none',
          borderLeftColor: 'primary.main',
          ml: entry.is_followup ? 3 : 0,
          minHeight: '120px',
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: 3,
            transform: 'translateY(-2px)',
            backgroundColor: 'action.hover',
          },
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
            <SearchIcon color="primary" sx={{ mt: 0.5 }} />

            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                {entry.user_query}
              </Typography>

              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                {/* Success/Error Status */}
                <Chip
                  icon={entry.success ? <CheckCircleIcon /> : <ErrorIcon />}
                  label={entry.success ? entry.results_summary : 'Error'}
                  size="small"
                  color={entry.success ? 'success' : 'error'}
                  variant="outlined"
                />

                {/* Timestamp */}
                <Chip
                  label={formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
                  size="small"
                  variant="outlined"
                />

                {/* Follow-up Indicator */}
                {entry.is_followup && (
                  <Chip
                    label="Follow-up"
                    size="small"
                    icon={<SubdirectoryArrowRightIcon />}
                    color="info"
                  />
                )}
              </Box>
            </Box>

            <ExpandMoreIcon sx={{ color: 'text.secondary' }} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  // Expanded or current state - show full results
  return (
    <Card
      sx={{
        borderLeft: entry.is_followup ? '4px solid' : 'none',
        borderLeftColor: 'primary.main',
        ml: entry.is_followup ? 3 : 0,
        borderTop: isCurrent ? '2px solid' : 'none',
        borderTopColor: 'primary.main',
        boxShadow: isCurrent ? 4 : 3,
      }}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <SearchIcon color="primary" sx={{ mr: 1, fontSize: 28 }} />

          <Typography variant="h5" sx={{ flex: 1, fontWeight: 600 }}>
            {entry.user_query}
          </Typography>

          {!isCurrent && (
            <IconButton onClick={onCollapse} size="large">
              <ExpandLessIcon />
            </IconButton>
          )}

          {isCurrent && (
            <Chip
              label="Current"
              color="primary"
              sx={{ fontWeight: 600 }}
            />
          )}
        </Box>

        {/* Metadata */}
        <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
          <Chip
            label={formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
            size="small"
            variant="outlined"
          />

          {entry.is_followup && (
            <ContextBadge
              previousQuery={entry.resolved_query}
              isFollowup={true}
              onClear={null}
            />
          )}
        </Box>

        {/* Full Results */}
        {results && (
          <Box>
            {/* Insight Card */}
            {agenticData?.explanation && (
              <InsightCard
                explanation={agenticData.explanation}
                keyDetails={agenticData.key_details}
              />
            )}

            {/* Data Visualization */}
            {results.results && results.results.length > 0 && results.columns && (
              <DataVisualization
                data={results.results}
                columns={results.columns}
              />
            )}

            {/* Data Table */}
            {results.results && results.columns && (
              <DataTable
                data={results.results}
                columns={results.columns}
              />
            )}

            {/* SQL Display */}
            {results.sql && (
              <SqlDisplay sql={results.sql} />
            )}

            {/* Validation Summary */}
            {(agenticData?.reflection || results.validation) && (
              <ValidationSummary
                reflection={agenticData?.reflection}
                securityValidation={results.validation}
              />
            )}
          </Box>
        )}

        {/* Error State */}
        {!entry.success && (
          <Box sx={{ p: 2, bgcolor: 'error.light', borderRadius: 1, color: 'error.dark' }}>
            <Typography variant="body1" sx={{ fontWeight: 600 }}>
              Query failed
            </Typography>
            <Typography variant="body2">
              {entry.results_summary || 'An error occurred while processing this query'}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}, (prevProps, nextProps) => {
  // Only re-render if expansion state or current status changes
  return prevProps.isExpanded === nextProps.isExpanded &&
         prevProps.isCurrent === nextProps.isCurrent;
});

TimelineCard.displayName = 'TimelineCard';

export default TimelineCard;
