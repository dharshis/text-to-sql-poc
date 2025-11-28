/**
 * App - Main application component with Chat Interface
 *
 * Enterprise-grade chat interface where users ask questions
 * and receive comprehensive AI-powered responses
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  ThemeProvider,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Chip,
  Switch,
  FormControlLabel,
  IconButton,
  Badge,
  Select,
  MenuItem,
  FormControl,
  Alert,
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon, Chat as ChatIcon } from '@mui/icons-material';
import theme from './styles/theme';
import ChatContainer from './components/ChatContainer';
import ChatInput from './components/ChatInput';
import ClarificationDialog from './components/ClarificationDialog';
import ConversationPanel from './components/ConversationPanel';
import IterationIndicator from './components/IterationIndicator';
import ContextBadge from './components/ContextBadge';
import { fetchClients, executeAgenticQuery, deleteSession, checkHealth } from './services/api';

function App() {
  // Client management
  const [clients, setClients] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState(null);
  const [clientsLoading, setClientsLoading] = useState(true);

  // Chat messages state
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Agentic mode and session
  const [agenticMode, setAgenticMode] = useState(true);
  const [sessionId, setSessionId] = useState(null);

  // Backend health status
  const [healthStatus, setHealthStatus] = useState(null);

  // Clarification dialog
  const [clarificationDialog, setClarificationDialog] = useState({
    open: false,
    questions: [],
    originalQuery: '',
    clientId: null,
  });

  // Conversation history panel
  const [conversationPanelOpen, setConversationPanelOpen] = useState(false);

  // Clarified query display
  const [clarifiedQuery, setClarifiedQuery] = useState(null);

  // Current agentic data for iterations
  const [currentAgenticData, setCurrentAgenticData] = useState(null);

  // Initialize session ID
  useEffect(() => {
    if (!sessionId) {
      const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
    }
  }, []);

  // Fetch clients on mount
  useEffect(() => {
    const loadClients = async () => {
      try {
        setClientsLoading(true);
        const clientList = await fetchClients();
        setClients(clientList);

        // Auto-select first client
        if (clientList && clientList.length > 0) {
          setSelectedClientId(clientList[0].client_id);
        }
      } catch (err) {
        console.error('Failed to fetch clients:', err);
      } finally {
        setClientsLoading(false);
      }
    };

    const checkBackendHealth = async () => {
      try {
        const health = await checkHealth();
        setHealthStatus(health);
      } catch (err) {
        console.error('Backend health check failed:', err);
        setHealthStatus({ status: 'unhealthy', error: err.message });
      }
    };

    loadClients();
    checkBackendHealth();
  }, []);

  // Keyboard shortcut for history panel (Cmd/Ctrl + H)
  useEffect(() => {
    const handleKeyPress = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'h') {
        e.preventDefault();
        setConversationPanelOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Handle query submission
  const handleQuerySubmit = async (query) => {
    if (!selectedClientId) return;

    // Clear clarified query unless it's the clarified query being submitted
    if (!clarifiedQuery || clarifiedQuery.combined !== query) {
      setClarifiedQuery(null);
    }

    // Add user message to chat
    const userMessage = {
      query,
      isUser: true,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      let data;

      if (agenticMode) {
        // Use agentic endpoint
        data = await executeAgenticQuery(query, sessionId, selectedClientId, 10);

        // Store current agentic data for iteration display
        setCurrentAgenticData({
          iterations: data.iterations,
          is_followup: data.is_followup,
          resolved_query: data.resolved_query,
        });

        // Handle clarification if needed
        if (data.needs_clarification) {
          setClarificationDialog({
            open: true,
            questions: data.questions || ['Please provide more details about your query.'],
            originalQuery: query,
            clientId: selectedClientId,
          });
          setLoading(false);
          return;
        }

        // Extract data from agentic response
        const executionResult = data.results || {};

        // Use security_validation if available (new), fallback to validation (old format)
        const securityValidation = data.security_validation || data.validation;

        // Transform validation format to match ValidationSummary component
        let validationForDisplay = null;

        if (securityValidation) {
          // If it's the full security validation (from sql_validator.py)
          if (securityValidation.passed !== undefined) {
            validationForDisplay = securityValidation; // Use as-is (already correct format)
          }
          // If it's the old agentic validation format
          else if (securityValidation.is_valid !== undefined) {
            validationForDisplay = {
              passed: securityValidation.is_valid,
              checks: securityValidation.issues && securityValidation.issues.length > 0
                ? securityValidation.issues.map((issue) => ({
                    name: 'Validation',
                    status: 'FAIL',
                    message: issue,
                  }))
                : [
                    {
                      name: 'SQL Quality',
                      status: 'PASS',
                      message: 'Query meets security requirements',
                    },
                  ],
              warnings: [],
            };
          }
        }

        // Create AI response message
        const aiMessage = {
          query,
          isUser: false,
          timestamp: new Date().toISOString(),
          explanation: data.explanation,
          reflection: data.reflection,
          sql: data.sql,
          results: executionResult.results || [],
          columns: executionResult.columns || [],
          rowCount: executionResult.row_count || 0,
          validation: validationForDisplay,
          isFollowup: data.is_followup || false,
          resolvedQuery: data.resolution_info?.interpreted_as || query,
        };

        setMessages((prev) => [...prev, aiMessage]);
      } else {
        // Classic mode - would need separate implementation
        console.log('Classic mode not yet implemented in chat interface');
      }
    } catch (err) {
      console.error('Query failed:', err);

      // Extract error details
      let errorMessage = 'Failed to process query';
      let errorDetails = err.message;
      let errorData = null;

      if (err.response?.data) {
        errorMessage = err.response.data.error || errorMessage;
        errorDetails = err.response.data.message || errorDetails;
        errorData = {
          sql: err.response.data.sql,
          validation: err.response.data.validation,
        };
      }

      // Add error message
      const aiErrorMessage = {
        query,
        isUser: false,
        timestamp: new Date().toISOString(),
        error: errorMessage,
        errorDetails: errorDetails,
        sql: errorData?.sql,
        validation: errorData?.validation,
      };

      setMessages((prev) => [...prev, aiErrorMessage]);
    } finally {
      setLoading(false);
      setCurrentAgenticData(null);
    }
  };

  // Handle clarification response
  const handleClarificationSubmit = async (response) => {
    setClarificationDialog({ ...clarificationDialog, open: false });

    // Resubmit query with additional context
    const enhancedQuery = `${clarificationDialog.originalQuery}\nAdditional context: ${response}`;

    // Show the clarified query to user
    setClarifiedQuery({
      original: clarificationDialog.originalQuery,
      clarification: response,
      combined: enhancedQuery,
    });

    await handleQuerySubmit(enhancedQuery);
  };

  // Clear conversation
  const handleClearConversation = async () => {
    const oldSessionId = sessionId;

    if (oldSessionId) {
      await deleteSession(oldSessionId);
    }

    // Generate new session
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);

    // Clear messages
    setMessages([]);
    setConversationPanelOpen(false);
  };

  // Build conversation history for panel
  const conversationHistory = messages
    .filter((m) => m.isUser)
    .map((m, index) => ({
      user_query: m.query,
      timestamp: m.timestamp,
      success: true,
      is_followup: messages[index * 2 + 1]?.isFollowup || false,
    }));

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* App Bar */}
        <AppBar position="static" elevation={1}>
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 0, mr: 4, fontWeight: 600 }}>
              Smart Insight Generator
            </Typography>

            {/* Client Selector */}
            <FormControl size="small" sx={{ minWidth: 200, mr: 2 }}>
              <Select
                value={selectedClientId || ''}
                onChange={(e) => setSelectedClientId(e.target.value)}
                disabled={clientsLoading}
                sx={{
                  color: 'white',
                  '.MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                  },
                  '& .MuiSvgIcon-root': {
                    color: 'white',
                  },
                }}
              >
                {clients.map((client) => (
                  <MenuItem key={client.client_id} value={client.client_id}>
                    {client.client_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ flexGrow: 1 }} />

            {/* Backend Health Status */}
            {healthStatus && (
              <Chip
                icon={healthStatus.status === 'healthy' ? <CheckCircle /> : <ErrorIcon />}
                label={`Backend: ${healthStatus.status || 'Unknown'}`}
                color={healthStatus.status === 'healthy' ? 'success' : 'error'}
                variant="outlined"
                sx={{
                  color: 'white',
                  borderColor: 'rgba(255, 255, 255, 0.3)',
                  '& .MuiChip-icon': {
                    color: 'white',
                  },
                }}
              />
            )}

            {/* Mode Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={agenticMode}
                  onChange={(e) => setAgenticMode(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': {
                      color: 'white',
                    },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                      backgroundColor: 'rgba(255, 255, 255, 0.5)',
                    },
                  }}
                />
              }
              label={
                <Typography variant="body2" sx={{ color: 'white' }}>
                  {agenticMode ? '🤖 AI Mode' : '⚡ Classic'}
                </Typography>
              }
            />

            {/* History Button */}
            {agenticMode && (
              <IconButton
                onClick={() => setConversationPanelOpen(true)}
                sx={{ ml: 2, color: 'white' }}
                aria-label="conversation history"
                title="View conversation history (Cmd/Ctrl + H)"
              >
                <Badge badgeContent={conversationHistory.length} color="error">
                  <ChatIcon />
                </Badge>
              </IconButton>
            )}
          </Toolbar>
        </AppBar>

        {/* Alerts and Status Area */}
        <Box sx={{ backgroundColor: 'background.default', borderBottom: '1px solid', borderColor: 'divider' }}>
          {/* Backend Connection Error */}
          {!healthStatus || (healthStatus.status !== 'healthy' && (
            <Alert severity="warning" sx={{ borderRadius: 0 }}>
              <Typography variant="subtitle2">Backend connection issue</Typography>
              <Typography variant="body2">
                Make sure the backend server is running on http://localhost:5000
              </Typography>
            </Alert>
          ))}

          {/* Context Badge (for follow-ups) */}
          {agenticMode && messages.length > 0 && messages[messages.length - 1]?.isFollowup && (
            <Box sx={{ px: 3, pt: 2 }}>
              <ContextBadge
                previousQuery={messages[messages.length - 1]?.resolvedQuery}
                isFollowup={messages[messages.length - 1]?.isFollowup}
                onClear={handleClearConversation}
              />
            </Box>
          )}

          {/* Clarified Query Display */}
          {clarifiedQuery && (
            <Box sx={{ px: 3, pt: 2 }}>
              <Alert severity="info" onClose={() => setClarifiedQuery(null)}>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                  📝 Your query was clarified:
                </Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Original:</strong> "{clarifiedQuery.original}"
                </Typography>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Your clarification:</strong> "{clarifiedQuery.clarification}"
                </Typography>
                <Typography variant="body2" sx={{ mt: 1, color: 'primary.main', fontWeight: 500 }}>
                  → Running: "{clarifiedQuery.combined}"
                </Typography>
              </Alert>
            </Box>
          )}

          {/* Iteration Indicator */}
          {loading && currentAgenticData?.iterations && (
            <Box sx={{ px: 3, pt: 2, pb: 2 }}>
              <IterationIndicator
                iteration={currentAgenticData.iterations}
                maxIterations={10}
              />
            </Box>
          )}
        </Box>

        {/* Chat Area */}
        <Box sx={{ flex: 1, overflow: 'hidden', backgroundColor: 'background.default' }}>
          <ChatContainer messages={messages} loading={loading} />
        </Box>

        {/* Input Area */}
        <ChatInput
          onSubmit={handleQuerySubmit}
          disabled={!selectedClientId || clientsLoading}
          loading={loading}
        />

        {/* Clarification Dialog */}
        <ClarificationDialog
          open={clarificationDialog.open}
          questions={clarificationDialog.questions}
          onSubmit={handleClarificationSubmit}
          onClose={() => setClarificationDialog({ ...clarificationDialog, open: false })}
        />

        {/* Conversation History Panel */}
        {agenticMode && (
          <ConversationPanel
            open={conversationPanelOpen}
            onClose={() => setConversationPanelOpen(false)}
            history={conversationHistory}
            currentQueryIndex={-1}
            onClearConversation={handleClearConversation}
            onQueryClick={(index) => console.log('Query clicked:', index)}
          />
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;
