import React from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Button,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import SubdirectoryArrowRightIcon from '@mui/icons-material/SubdirectoryArrowRight';
import { formatDistanceToNow } from 'date-fns';

/**
 * Conversation History Panel
 * Story 7.3 - AC1-AC5
 *
 * Professional slide-out panel showing conversation history with:
 * - Visual follow-up hierarchy (indentation)
 * - Status chips (success/error)
 * - Relative timestamps
 * - Current query highlight
 * - Clear conversation button
 */
const ConversationPanel = ({
  open,
  onClose,
  history = [],
  currentQueryIndex,
  onClearConversation,
  onQueryClick,
}) => {
  const handleQueryClick = (index) => {
    if (onQueryClick) {
      onQueryClick(index);
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: 350,
          boxSizing: 'border-box',
        },
      }}
    >
      {/* Header (AC2) */}
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            💬 Conversation
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        <Typography variant="caption" color="text.secondary">
          Session: {history.length} {history.length === 1 ? 'query' : 'queries'}
        </Typography>
      </Box>

      <Divider />

      {/* Query List (AC3) */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {history.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
            No queries yet
          </Typography>
        ) : (
          <List sx={{ p: 0 }}>
            {history.map((entry, index) => {
              const isCurrent = index === currentQueryIndex;
              const isFollowup = entry.is_followup || false;
              const success = entry.success !== false;

              // Format query text (truncate if needed)
              const queryText = entry.user_query || 'Unknown query';
              const displayText = queryText.length > 50 ? queryText.substring(0, 50) + '...' : queryText;

              // Format timestamp
              let timeAgo = 'Just now';
              if (entry.timestamp) {
                try {
                  const date = new Date(entry.timestamp);
                  timeAgo = formatDistanceToNow(date, { addSuffix: true });
                } catch (e) {
                  timeAgo = 'Unknown time';
                }
              }

              return (
                <ListItem
                  key={index}
                  onClick={() => handleQueryClick(index)}
                  sx={{
                    mb: 1,
                    p: 1.5,
                    borderRadius: 1,
                    cursor: 'pointer',
                    backgroundColor: isCurrent ? 'action.selected' : 'transparent',
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                    pl: isFollowup ? 4 : 2, // Indent follow-ups
                  }}
                >
                  <Box sx={{ width: '100%' }}>
                    {/* Query icon + text */}
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 0.5 }}>
                      <Box sx={{ mr: 1, mt: 0.2 }}>
                        {isFollowup ? (
                          <SubdirectoryArrowRightIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                        ) : (
                          <SearchIcon sx={{ fontSize: 18, color: 'primary.main' }} />
                        )}
                      </Box>
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: isCurrent ? 600 : 400,
                          flexGrow: 1,
                          wordBreak: 'break-word',
                        }}
                      >
                        {displayText}
                      </Typography>
                    </Box>

                    {/* Status chips */}
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1, ml: 3 }}>
                      {/* Current indicator */}
                      {isCurrent && (
                        <Chip
                          label="⚡ Viewing"
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      )}

                      {/* Success/error chip */}
                      {success ? (
                        <Chip
                          label={`✅ ${entry.results_summary || 'Success'}`}
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                      ) : (
                        <Chip
                          label="⚠️ Error"
                          size="small"
                          color="error"
                          variant="outlined"
                        />
                      )}

                      {/* Timestamp chip */}
                      <Chip
                        label={timeAgo}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                </ListItem>
              );
            })}
          </List>
        )}
      </Box>

      {/* Footer (AC4) */}
      <Divider />
      <Box sx={{ p: 2 }}>
        <Button
          variant="outlined"
          color="error"
          fullWidth
          disabled={history.length === 0}
          onClick={onClearConversation}
        >
          Clear Conversation
        </Button>
      </Box>
    </Drawer>
  );
};

export default ConversationPanel;
