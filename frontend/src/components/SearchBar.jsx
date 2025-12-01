/**
 * SearchBar component - Conversational UI interface.
 *
 * Chat-style interface for natural language queries.
 * Client selection is handled by the ClientSelector component.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Avatar,
} from '@mui/material';
import { Send as SendIcon, Person as PersonIcon, SmartToy as BotIcon } from '@mui/icons-material';

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: 'Hi! I\'m your Smart Insight Generator. I can help you analyze:\n\n📊 Brand Portfolio Performance\n💰 Price Tier Strategies (Premium vs Mass)\n📈 Sales Trends & Growth\n🌍 Geographic Analysis\n📦 Distribution Effectiveness',
  timestamp: new Date(),
};

const SearchBar = ({ clientId, onSubmit, loading, disabled, resetTrigger, clarificationQuestions, onClarificationResponse }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [awaitingClarification, setAwaitingClarification] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reset messages when resetTrigger changes
  useEffect(() => {
    if (resetTrigger !== undefined && resetTrigger !== null) {
      setMessages([{ ...INITIAL_MESSAGE, timestamp: new Date() }]);
      setQuery('');
      setAwaitingClarification(false);
      console.log('Chat UI reset to initial state');
    }
  }, [resetTrigger]);

  // Add clarification questions as chat messages when they arrive
  useEffect(() => {
    if (clarificationQuestions && clarificationQuestions.length > 0 && !awaitingClarification) {
      // Remove the "Analyzing your query..." message if it exists
      setMessages(prev => {
        const filtered = prev.filter(msg => !(msg.isThinking && msg.content === 'Analyzing your query...'));
        
        const clarificationMessage = {
          role: 'assistant',
          content: 'I need a bit more information to help you better:\n\n' + 
                   clarificationQuestions.map((q, i) => `${i + 1}. ${q}`).join('\n') +
                   '\n\nPlease provide additional details in your response.',
          timestamp: new Date(),
          isClarification: true,
        };
        
        return [...filtered, clarificationMessage];
      });
      setAwaitingClarification(true);
    }
  }, [clarificationQuestions, awaitingClarification]);

  // Update "Analyzing your query..." message when loading completes
  useEffect(() => {
    if (!loading) {
      // Find the last "thinking" message and update it
      setMessages(prev => {
        const updated = [...prev];
        // Find the last message with isThinking flag
        for (let i = updated.length - 1; i >= 0; i--) {
          if (updated[i].isThinking && updated[i].content === 'Analyzing your query...') {
            updated[i] = {
              ...updated[i],
              content: 'Done fetching results',
              isThinking: false,
            };
            break;
          }
        }
        return updated;
      });
      
      // Reset clarification state when loading completes (unless we're awaiting clarification)
      if (!awaitingClarification) {
        setAwaitingClarification(false);
      }
    }
  }, [loading, awaitingClarification]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (clientId && query.trim() && !loading) {
      // Add user message to chat
      const userMessage = {
        role: 'user',
        content: query.trim(),
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);

      // If we're awaiting clarification, handle it as a clarification response
      if (awaitingClarification && onClarificationResponse) {
        onClarificationResponse(query.trim());
        setAwaitingClarification(false);
        setQuery('');
        return;
      }

      // Otherwise, submit as normal query
      onSubmit(query, clientId);

      // Clear input
      setQuery('');

      // Add thinking message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Analyzing your query...',
        timestamp: new Date(),
        isThinking: true,
      }]);
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift key)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSubmitDisabled) {
        handleSubmit(e);
      }
    }
  };

  const isSubmitDisabled = !clientId || !query.trim() || loading || disabled;

  return (
    <Paper elevation={3} sx={{ display: 'flex', flexDirection: 'column', height: '500px', mb: 3 }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider', backgroundColor: 'primary.main' }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: 'white', display: 'flex', alignItems: 'center', gap: 1 }}>
          <BotIcon /> Natural Language Query Interface
        </Typography>
      </Box>

      {/* Messages Container */}
      <Box
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          p: 2,
          backgroundColor: '#f5f5f5',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              gap: 1.5,
              alignItems: 'flex-start',
              flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
            }}
          >
            {/* Avatar */}
            <Avatar
              sx={{
                bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                width: 36,
                height: 36,
              }}
            >
              {message.role === 'user' ? <PersonIcon fontSize="small" /> : <BotIcon fontSize="small" />}
            </Avatar>

            {/* Message Bubble */}
            <Box
              sx={{
                maxWidth: '70%',
                bgcolor: message.role === 'user' ? 'primary.light' : 'white',
                color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                p: 1.5,
                borderRadius: 2,
                boxShadow: 1,
                opacity: message.isThinking ? 0.7 : 1,
                fontStyle: message.isThinking ? 'italic' : 'normal',
              }}
            >
              <Typography variant="body1" sx={{ wordBreak: 'break-word', whiteSpace: 'pre-line' }}>
                {message.content}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.7, mt: 0.5, display: 'block' }}>
                {message.timestamp.toLocaleTimeString()}
              </Typography>
            </Box>
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Container */}
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          borderTop: '1px solid',
          borderColor: 'divider',
          backgroundColor: 'background.paper',
        }}
      >
        {disabled && (
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
            Please select a client above to start querying
          </Typography>
        )}
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={3}
            placeholder={awaitingClarification ? "Please provide additional details..." : "Type your message here..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading || disabled}
            variant="outlined"
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
              },
            }}
          />
          <IconButton
            type="submit"
            color="primary"
            disabled={isSubmitDisabled}
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&:disabled': {
                bgcolor: 'action.disabledBackground',
              },
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Paper>
  );
};

export default SearchBar;
