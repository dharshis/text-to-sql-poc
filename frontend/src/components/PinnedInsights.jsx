/**
 * PinnedInsights Component
 *
 * Displays a list of pinned insights in the left panel for quick reference.
 * Allows users to view and unpin saved insights.
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Collapse,
  Card,
  CardContent,
  Tooltip,
  Chip,
} from '@mui/material';
import PushPinIcon from '@mui/icons-material/PushPin';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { formatDistanceToNow } from 'date-fns';

const PinnedInsights = ({ pinnedInsights, onUnpin }) => {
  const [expanded, setExpanded] = useState(true);
  const [expandedInsights, setExpandedInsights] = useState({});

  const toggleInsight = (insightId) => {
    setExpandedInsights(prev => ({
      ...prev,
      [insightId]: !prev[insightId]
    }));
  };

  if (pinnedInsights.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mb: 3 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 1.5,
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PushPinIcon sx={{ fontSize: 20, color: '#4A90E2' }} />
          <Typography variant="subtitle2" fontWeight={600} color="#2C3E50">
            Pinned Insights ({pinnedInsights.length})
          </Typography>
        </Box>
        <IconButton size="small" sx={{ color: '#4A90E2' }}>
          {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
        </IconButton>
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {pinnedInsights.map((insight) => {
            const isExpanded = expandedInsights[insight.id];
            const timeAgo = formatDistanceToNow(new Date(insight.timestamp), { addSuffix: true });

            return (
              <Card
                key={insight.id}
                sx={{
                  boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.06)',
                  border: '1px solid #E8EDF2',
                  borderRadius: 2,
                  transition: 'all 0.15s ease',
                  '&:hover': {
                    boxShadow: '0 4px 8px 0 rgba(0, 0, 0, 0.08)',
                    borderColor: '#4A90E2',
                  },
                }}
              >
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  {/* Header */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        sx={{
                          color: '#2C3E50',
                          mb: 0.5,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                        }}
                      >
                        {insight.userQuery}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 0.5 }}>
                        <Chip
                          label={insight.client}
                          size="small"
                          sx={{
                            height: 20,
                            fontSize: '0.7rem',
                            backgroundColor: '#EBF2FA',
                            color: '#4A90E2',
                          }}
                        />
                        <Chip
                          label={timeAgo}
                          size="small"
                          sx={{
                            height: 20,
                            fontSize: '0.7rem',
                            backgroundColor: '#F5F7FA',
                            color: '#7B8794',
                          }}
                        />
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 0.5, ml: 1 }}>
                      <Tooltip title="Expand/Collapse">
                        <IconButton
                          size="small"
                          onClick={() => toggleInsight(insight.id)}
                          sx={{ color: '#4A90E2' }}
                        >
                          {isExpanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Unpin">
                        <IconButton
                          size="small"
                          onClick={() => onUnpin(insight.id)}
                          sx={{ color: '#EF4444' }}
                        >
                          <DeleteOutlineIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>

                  {/* Expanded Content */}
                  <Collapse in={isExpanded}>
                    <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid #E8EDF2' }}>
                      <Typography
                        variant="caption"
                        sx={{
                          color: '#5A646F',
                          display: 'block',
                          mb: 1,
                          fontSize: '0.75rem',
                          lineHeight: 1.4,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                        }}
                      >
                        {insight.explanation}
                      </Typography>

                      {insight.keyDetails && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" sx={{ color: '#7B8794', fontWeight: 600, display: 'block', mb: 0.5 }}>
                            Dataset: {insight.keyDetails.dataset}
                          </Typography>
                          {insight.keyDetails.result && (
                            <Typography variant="caption" sx={{ color: '#7B8794', display: 'block' }}>
                              Result: {insight.keyDetails.result}
                            </Typography>
                          )}
                        </Box>
                      )}
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      </Collapse>
    </Box>
  );
};

export default PinnedInsights;
