/**
 * ChatContainer Component
 *
 * Displays the chat message history with auto-scroll functionality
 */

import React, { useRef, useEffect } from 'react';
import { Box, Typography, CircularProgress, Fab, Chip } from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import ChatMessage from './ChatMessage';

const ChatContainer = ({ messages, loading, onSuggestedQuestionClick }) => {
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);
  const [showScrollButton, setShowScrollButton] = React.useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages.length]);

  // Check if user has scrolled up
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollButton(!isAtBottom);
    }
  };

  // Empty state
  if (messages.length === 0 && !loading) {
    const exampleQuestions = [
      "Show me the top 5 products by revenue",
      "What are the monthly sales trends?",
      "Compare revenue across different regions",
      "Show total sales for each category"
    ];

    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          width: '100%',
          px: 4,
          textAlign: 'center',
        }}
      >
        <Box
          sx={{
            width: 120,
            height: 120,
            borderRadius: '50%',
            backgroundColor: 'primary.light',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 3,
            opacity: 0.2,
          }}
        >
          <Typography variant="h1" sx={{ fontSize: '4rem' }}>
            💬
          </Typography>
        </Box>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
          Welcome to Smart Insight Generator
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 500, mb: 4 }}>
          Ask questions about your data in natural language. I'll generate smart insights based on results from your query.
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontWeight: 500 }}>
            Try asking:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, justifyContent: 'center', maxWidth: 600 }}>
            {exampleQuestions.map((question, index) => (
              <Chip
                key={index}
                label={question}
                onClick={() => onSuggestedQuestionClick && onSuggestedQuestionClick(question, true)}
                variant="outlined"
                sx={{
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  height: 'auto',
                  py: 1.5,
                  px: 2,
                  transition: 'all 0.2s ease',
                  '& .MuiChip-label': {
                    whiteSpace: 'normal',
                    textAlign: 'center',
                  },
                  '&.MuiChip-clickable:hover': {
                    backgroundColor: 'primary.main',
                    borderColor: 'primary.main',
                    color: 'white',
                    transform: 'translateY(-2px)',
                    boxShadow: 3,
                  },
                  '&:hover': {
                    backgroundColor: 'primary.main',
                    borderColor: 'primary.main',
                    color: 'white',
                    transform: 'translateY(-2px)',
                    boxShadow: 3,
                  },
                }}
              />
            ))}
          </Box>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ position: 'relative', height: '100%', width: '100%' }}>
      <Box
        ref={containerRef}
        onScroll={handleScroll}
        sx={{
          height: '100%',
          width: '100%',
          overflowY: 'auto',
          overflowX: 'hidden',
          px: 3,
          py: 4,
          boxSizing: 'border-box',
        }}
      >
        {messages.map((message, index) => {
          // Check if this is the latest AI message
          const isLatestAI = !message.isUser && index === messages.length - 1;
          return (
            <ChatMessage
              key={index}
              message={message}
              isUser={message.isUser}
              isLatest={isLatestAI}
              onSuggestedQuestionClick={onSuggestedQuestionClick}
            />
          );
        })}

        {/* Loading indicator */}
        {loading && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              mb: 4,
            }}
          >
            <CircularProgress size={24} />
            <Typography variant="body2" color="text.secondary">
              Analyzing your query...
            </Typography>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <Fab
          size="small"
          color="primary"
          sx={{
            position: 'absolute',
            bottom: 16,
            right: 16,
            boxShadow: 3,
          }}
          onClick={scrollToBottom}
        >
          <KeyboardArrowDownIcon />
        </Fab>
      )}
    </Box>
  );
};

export default ChatContainer;
