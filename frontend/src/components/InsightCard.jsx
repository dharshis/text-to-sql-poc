/**
 * InsightCard Component
 * Architecture Reference: Section 9.2 (Component Specifications)
 * 
 * PRIMARY component for displaying natural language explanations.
 * Positioned at the TOP of results for maximum visibility.
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Collapse,
  IconButton,
  Box,
} from '@mui/material';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const InsightCard = ({ explanation }) => {
  const [expanded, setExpanded] = useState(true);

  if (!explanation) {
    return null;
  }

  return (
    <Card
      sx={{
        mb: 3,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        boxShadow: 3,
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <LightbulbIcon sx={{ fontSize: 28, color: '#ffd700' }} />
            <Typography variant="h6" component="div" fontWeight="bold">
              Key Insights
            </Typography>
          </Box>
          <IconButton
            onClick={() => setExpanded(!expanded)}
            sx={{ color: 'white' }}
            aria-label={expanded ? 'collapse' : 'expand'}
          >
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={expanded}>
          <Typography
            variant="body1"
            sx={{
              mt: 2,
              fontSize: '16px',
              lineHeight: 1.6,
              whiteSpace: 'pre-line',
            }}
          >
            {explanation}
          </Typography>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default InsightCard;

