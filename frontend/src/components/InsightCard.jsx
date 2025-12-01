/**
 * InsightCard Component
 * Architecture Reference: Section 9.2 (Component Specifications)
 *
 * PRIMARY component for displaying natural language explanations.
 * Positioned at the TOP of results for maximum visibility.
 * Supports Markdown formatting for rich text display.
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Collapse,
  IconButton,
  Box,
  Tooltip,
} from '@mui/material';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import PushPinIcon from '@mui/icons-material/PushPin';
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined';
import ReactMarkdown from 'react-markdown';

const InsightCard = ({ explanation, keyDetails, onPin, isPinned }) => {
  const [expanded, setExpanded] = useState(true);

  if (!explanation) {
    return null;
  }

  return (
    <Card
      sx={{
        mb: 3,
        width: '100%',
        maxWidth: '100%',
        boxSizing: 'border-box',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        boxShadow: 3,
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <LightbulbIcon sx={{ fontSize: 28, color: '#ffd700' }} />
            <Typography variant="h6" component="div" fontWeight="bold">
              Key Insights
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={0.5}>
            {onPin && (
              <Tooltip title={isPinned ? "Unpin insight" : "Pin insight for future reference"}>
                <IconButton
                  onClick={onPin}
                  sx={{ color: isPinned ? '#ffd700' : 'rgba(255, 255, 255, 0.7)' }}
                  aria-label={isPinned ? 'unpin' : 'pin'}
                >
                  {isPinned ? <PushPinIcon /> : <PushPinOutlinedIcon />}
                </IconButton>
              </Tooltip>
            )}
            <IconButton
              onClick={() => setExpanded(!expanded)}
              sx={{ color: 'white' }}
              aria-label={expanded ? 'collapse' : 'expand'}
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>

        <Collapse in={expanded}>
          <Box
            sx={{
              mt: 2,
              fontSize: '16px',
              lineHeight: 1.6,
              '& p': {
                margin: '0 0 1em 0',
                '&:last-child': {
                  marginBottom: 0,
                },
              },
              '& ul, & ol': {
                margin: '0 0 1em 0',
                paddingLeft: '1.5em',
              },
              '& li': {
                marginBottom: '0.5em',
              },
              '& h1, & h2, & h3, & h4, & h5, & h6': {
                margin: '1em 0 0.5em 0',
                fontWeight: 600,
                '&:first-of-type': {
                  marginTop: 0,
                },
              },
              '& h1': { fontSize: '1.5em' },
              '& h2': { fontSize: '1.3em' },
              '& h3': { fontSize: '1.1em' },
              '& code': {
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '0.9em',
                fontFamily: 'monospace',
              },
              '& pre': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                padding: '12px',
                borderRadius: '8px',
                overflow: 'auto',
                margin: '1em 0',
              },
              '& pre code': {
                backgroundColor: 'transparent',
                padding: 0,
              },
              '& blockquote': {
                borderLeft: '3px solid rgba(255, 255, 255, 0.5)',
                paddingLeft: '1em',
                margin: '1em 0',
                fontStyle: 'italic',
              },
              '& strong': {
                fontWeight: 700,
              },
              '& em': {
                fontStyle: 'italic',
              },
              '& a': {
                color: '#ffd700',
                textDecoration: 'underline',
                '&:hover': {
                  color: '#ffed4e',
                },
              },
              '& hr': {
                border: 'none',
                borderTop: '1px solid rgba(255, 255, 255, 0.3)',
                margin: '1.5em 0',
              },
              '& table': {
                borderCollapse: 'collapse',
                width: '100%',
                margin: '1em 0',
              },
              '& th, & td': {
                border: '1px solid rgba(255, 255, 255, 0.3)',
                padding: '8px 12px',
                textAlign: 'left',
              },
              '& th': {
                fontWeight: 600,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
              },
            }}
          >
            <ReactMarkdown>{explanation}</ReactMarkdown>
            
            {/* Key Details Section */}
            {keyDetails && (
              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid rgba(255,255,255,0.3)' }}>
                <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1.5 }}>
                  Key details:
                </Typography>
                <Box sx={{ pl: 2, fontSize: '14px' }}>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    - <strong>Dataset used:</strong> {keyDetails.dataset}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    - <strong>Filters applied:</strong>
                  </Typography>
                  {keyDetails.filters_applied && keyDetails.filters_applied.map((filter, idx) => (
                    <Typography key={idx} variant="body2" sx={{ pl: 2, mb: 0.5 }}>
                      - {filter}
                    </Typography>
                  ))}
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    - <strong>Result:</strong> {keyDetails.result}
                  </Typography>
                </Box>
              </Box>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default InsightCard;


