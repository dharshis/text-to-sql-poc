/**
 * App - Main application component
 *
 * Orchestrates the text-to-SQL POC interface:
 * - Fetches clients on mount
 * - Handles query submission
 * - Manages loading/error states
 * - Displays results
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Alert,
  ThemeProvider,
  CssBaseline,
  Chip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import theme from './styles/theme';
import SearchBar from './components/SearchBar';
import ResultsDisplay from './components/ResultsDisplay';
import InsightCard from './components/InsightCard';
import ClarificationDialog from './components/ClarificationDialog';
import IterationIndicator from './components/IterationIndicator';
import ContextBadge from './components/ContextBadge';
import ConversationPanel from './components/ConversationPanel';
import ClientSelector from './components/ClientSelector';
import PinnedInsights from './components/PinnedInsights';
import { fetchClients, submitQuery, checkHealth, executeAgenticQuery, deleteSession } from './services/api';
import ChatIcon from '@mui/icons-material/Chat';
import { Badge, IconButton } from '@mui/material';

function App() {
  const [clients, setClients] = useState([]);
  const [selectedClientId, setSelectedClientId] = useState(null);
  const [clientsLoading, setClientsLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);

  // Agentic mode state (Architecture Section 9.3)
  const [agenticMode, setAgenticMode] = useState(true); // Default to agentic
  const [sessionId, setSessionId] = useState(null);
  const [clarificationDialog, setClarificationDialog] = useState({
    open: false,
    questions: [],
    originalQuery: '',
    clientId: null,
  });
  // Clarification state for chat interface
  const [clarificationQuestions, setClarificationQuestions] = useState([]);
  const [originalQueryForClarification, setOriginalQueryForClarification] = useState('');
  const [clarificationClientId, setClarificationClientId] = useState(null);
  const [agenticData, setAgenticData] = useState(null); // Explanation, reflection, etc.

  // Story 7.3: Conversation history state (AC6)
  const [conversationHistory, setConversationHistory] = useState([]);
  const [conversationPanelOpen, setConversationPanelOpen] = useState(false);
  const [currentQueryIndex, setCurrentQueryIndex] = useState(-1);

  // Chat reset trigger (incremented to reset SearchBar messages)
  const [chatResetTrigger, setChatResetTrigger] = useState(0);

  // Clarified query display
  const [clarifiedQuery, setClarifiedQuery] = useState(null);

  // Pinned insights state (with localStorage persistence)
  const [pinnedInsights, setPinnedInsights] = useState(() => {
    const saved = localStorage.getItem('pinnedInsights');
    return saved ? JSON.parse(saved) : [];
  });

  // Save pinned insights to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('pinnedInsights', JSON.stringify(pinnedInsights));
  }, [pinnedInsights]);

  // Initialize session ID on mount
  useEffect(() => {
    if (!sessionId) {
      const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      console.log(`Session initialized: ${newSessionId}`);
    }
  }, []);

  // Fetch clients on mount
  useEffect(() => {
    const loadClients = async () => {
      try {
        setClientsLoading(true);
        const clientList = await fetchClients();
        setClients(clientList);

        // Auto-select first client if available
        if (clientList && clientList.length > 0) {
          setSelectedClientId(clientList[0].client_id);
        }
      } catch (err) {
        console.error('Failed to fetch clients:', err);
        setError({
          message: 'Failed to load clients',
          details: err.message || 'Could not connect to backend',
        });
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

  // Story 7.3: Keyboard shortcut for history panel (AC8: Cmd/Ctrl + H)
  useEffect(() => {
    const handleKeyPress = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'h') {
        e.preventDefault();
        setConversationPanelOpen(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Handle query submission (Architecture Section 9.3)
  const handleQuerySubmit = async (query, clientId) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setAgenticData(null);

    // Clear clarified query unless it's the clarified query being submitted
    if (!clarifiedQuery || clarifiedQuery.combined !== query) {
      setClarifiedQuery(null);
    }

    try {
      let data;

      if (agenticMode) {
        // Use agentic endpoint
        console.log(`Executing agentic query with session: ${sessionId}`);
        data = await executeAgenticQuery(query, sessionId, clientId, 10);

        // Handle clarification if needed - pass to chat instead of dialog
        if (data.needs_clarification) {
          setClarificationQuestions(data.questions || ['Please provide more details about your query.']);
          setOriginalQueryForClarification(query);
          setClarificationClientId(clientId);
          setLoading(false);
          return;
        }

        // Clear clarification state when query succeeds
        setClarificationQuestions([]);
        setOriginalQueryForClarification('');
        setClarificationClientId(null);

        // Store agentic-specific data
        setAgenticData({
          explanation: data.explanation,
          reflection: data.reflection,
          iterations: data.iterations,
          is_followup: data.is_followup,
          resolved_query: data.resolved_query,
          key_details: data.key_details,
        });

        // Transform agentic response to match ResultsDisplay format
        // Note: data.results is QueryExecutor response with nested structure
        const executionResult = data.results || {};

        // Use security_validation if available (new), fallback to validation (old format)
        const securityValidation = data.security_validation || data.validation;

        // Transform validation format to match ValidationMetrics component
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
                ? securityValidation.issues.map(issue => ({
                    name: 'Validation',
                    status: 'FAIL',
                    message: issue
                  }))
                : [{
                    name: 'SQL Quality',
                    status: 'PASS',
                    message: 'Query meets security requirements'
                  }],
              warnings: []
            };
          }
        }

        setResults({
          sql: data.sql,
          results: executionResult.results || [],  // Extract actual data array
          columns: executionResult.columns || [],
          row_count: executionResult.row_count || 0,
          validation: validationForDisplay,
          method: 'agentic',
        });

        // Story 7.3: Add to conversation history (AC6)
        const historyEntry = {
          user_query: query,
          resolved_query: data.resolution_info?.interpreted_as || query,
          timestamp: new Date().toISOString(),
          success: data.success !== false,
          results_summary: executionResult.row_count
            ? `${executionResult.row_count} rows`
            : 'No results',
          is_followup: data.is_followup || false
        };

        setConversationHistory(prev => [...prev, historyEntry]);
        setCurrentQueryIndex(conversationHistory.length); // Index of newly added entry
      } else {
        // Use classic endpoint
        data = await submitQuery(query, clientId);
        setResults(data);
      }

    } catch (err) {
      console.error('Query failed:', err);

      // Extract error details from response
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

      setError({
        message: errorMessage,
        details: errorDetails,
        data: errorData,
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle clarification response from chat
  const handleClarificationResponse = async (response) => {
    // Create a more natural query that incorporates the clarification
    // Format: Original query + clarification in a clear, natural way
    const enhancedQuery = `${originalQueryForClarification}. Additional information: ${response}`;

    // Show the clarified query to user
    setClarifiedQuery({
      original: originalQueryForClarification,
      clarification: response,
      combined: enhancedQuery
    });

    // Clear clarification state
    setClarificationQuestions([]);
    setOriginalQueryForClarification('');
    setClarificationClientId(null);

    await handleQuerySubmit(enhancedQuery, clarificationClientId);
  };

  // Handle clarification response (for dialog - kept for backward compatibility)
  const handleClarificationSubmit = async (response) => {
    setClarificationDialog({ ...clarificationDialog, open: false });

    // Resubmit query with additional context
    const enhancedQuery = `${clarificationDialog.originalQuery}\nAdditional context: ${response}`;

    // Show the clarified query to user
    setClarifiedQuery({
      original: clarificationDialog.originalQuery,
      clarification: response,
      combined: enhancedQuery
    });

    await handleQuerySubmit(enhancedQuery, clarificationDialog.clientId);
  };

  // Story 7.3: Handle clear conversation (AC6)
  // Enhanced: Deletes old session from backend memory before creating new one
  const handleClearConversation = async () => {
    const oldSessionId = sessionId;

    // Delete old session from backend (ensures complete memory cleanup)
    if (oldSessionId) {
      console.log(`Deleting old session: ${oldSessionId}`);
      await deleteSession(oldSessionId);
    }

    // Generate new session ID
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);

    // Clear frontend history
    setConversationHistory([]);
    setCurrentQueryIndex(-1);
    setAgenticData(null);
    setClarifiedQuery(null);
    setResults(null);
    setError(null);
    
    // Clear clarification state
    setClarificationQuestions([]);
    setOriginalQueryForClarification('');
    setClarificationClientId(null);

    // Reset chat UI (triggers SearchBar to show initial message)
    setChatResetTrigger(prev => prev + 1);

    // Close panel
    setConversationPanelOpen(false);

    console.log(`✅ Session cleared and deleted from backend`);
    console.log(`✅ New session created: ${newSessionId}`);
    console.log(`✅ No memory of previous session exists`);
    console.log(`✅ Chat UI reset to initial state`);
  };

  // Handle pinning an insight
  const handlePinInsight = () => {
    if (!agenticData?.explanation) return;

    const insightId = `insight-${Date.now()}`;
    const pinnedInsight = {
      id: insightId,
      query: results?.sql || '',
      userQuery: agenticData?.resolved_query || '',
      explanation: agenticData.explanation,
      keyDetails: agenticData.key_details,
      timestamp: new Date().toISOString(),
      client: clients.find(c => c.client_id === selectedClientId)?.client_name || 'Unknown',
    };

    setPinnedInsights(prev => [pinnedInsight, ...prev]);
    console.log('Insight pinned:', insightId);
  };

  // Handle unpinning an insight
  const handleUnpinInsight = (insightId) => {
    setPinnedInsights(prev => prev.filter(insight => insight.id !== insightId));
    console.log('Insight unpinned:', insightId);
  };

  // Check if current insight is pinned
  const isCurrentInsightPinned = () => {
    if (!agenticData?.explanation) return false;
    return pinnedInsights.some(insight =>
      insight.explanation === agenticData.explanation &&
      insight.query === results?.sql
    );
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
        {/* Left Panel - Search Bar (40%) */}
        <Box
          sx={{
            width: '40%',
            flexShrink: 0,
            height: '100vh',
            borderRight: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'background.paper',
            overflowY: 'auto',
            overflowX: 'hidden'
          }}
        >
          <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Title */}
            <Typography variant="h5" component="h1" sx={{ fontWeight: 600 }}>
              Smart Insight Generator
            </Typography>

            {/* Client Selector */}
            <ClientSelector
              clients={clients}
              selectedClientId={selectedClientId}
              onClientChange={setSelectedClientId}
              loading={clientsLoading}
            />

            {/* Search Bar */}
            <SearchBar
              clientId={selectedClientId}
              onSubmit={handleQuerySubmit}
              loading={loading}
              disabled={!selectedClientId}
              resetTrigger={chatResetTrigger}
              clarificationQuestions={clarificationQuestions}
              onClarificationResponse={handleClarificationResponse}
            />

            {/* Pinned Insights */}
            <PinnedInsights
              pinnedInsights={pinnedInsights}
              onUnpin={handleUnpinInsight}
            />

            {/* Conversation History Button */}
            {agenticMode && conversationHistory.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Box
                  onClick={() => setConversationPanelOpen(true)}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 2,
                    border: '1px solid #E8EDF2',
                    borderRadius: 2,
                    backgroundColor: '#FFFFFF',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    '&:hover': {
                      borderColor: '#4A90E2',
                      boxShadow: '0 2px 8px rgba(74, 144, 226, 0.15)',
                    },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <ChatIcon sx={{ fontSize: 22, color: '#4A90E2' }} />
                    <Box>
                      <Typography variant="subtitle2" fontWeight={600} color="#2C3E50">
                        Conversation History
                      </Typography>
                      <Typography variant="caption" color="#7B8794">
                        View past queries and results
                      </Typography>
                    </Box>
                  </Box>
                  <Badge badgeContent={conversationHistory.length} color="primary">
                    <Box sx={{ width: 24, height: 24 }} />
                  </Badge>
                </Box>
              </Box>
            )}

            {/* Iteration Indicator */}
            {loading && agenticData?.iterations && (
              <IterationIndicator
                iteration={agenticData.iterations}
                maxIterations={10}
              />
            )}
          </Box>
        </Box>

        {/* Right Panel - All Other Components (60%) */}
        <Box
          sx={{
            width: '60%',
            flexShrink: 0,
            height: '100vh',
            overflowY: 'auto',
            overflowX: 'hidden',
            backgroundColor: 'background.default'
          }}
        >
          <Box sx={{ py: 4, px: 3, width: '100%', boxSizing: 'border-box' }}>
            {/* Header */}
            <Box sx={{ mb: 4, width: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1, flexWrap: 'wrap', gap: 2 }}>
                <Typography variant="h4" component="h2" sx={{ fontWeight: 600 }}>
                  Insights
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                  {/* Agentic Mode Toggle */}
                  <FormControlLabel
                    control={
                      <Switch
                        checked={agenticMode}
                        onChange={(e) => setAgenticMode(e.target.checked)}
                        color="primary"
                      />
                    }
                    label={agenticMode ? '🤖 Agentic Mode' : '⚡ Classic Mode'}
                  />

                  {/* Backend Health Status */}
                  {healthStatus && (
                    <Chip
                      icon={healthStatus.status === 'healthy' ? <CheckCircle /> : <ErrorIcon />}
                      label={`Backend: ${healthStatus.status || 'Unknown'}`}
                      color={healthStatus.status === 'healthy' ? 'success' : 'error'}
                      variant="outlined"
                    />
                  )}
                </Box>
              </Box>

              <Typography variant="body1" color="text.secondary">
                {agenticMode
                  ? '🤖 AI agents clarify, plan, and explain your queries with natural language insights'
                  : '⚡ Classic mode: Fast SQL generation without agent workflow'
                }
              </Typography>
            </Box>

            {/* Backend Connection Error */}
            {!healthStatus || healthStatus.status !== 'healthy' && (
              <Alert severity="warning" sx={{ mb: 3 }}>
                <Typography variant="subtitle2">
                  Backend connection issue
                </Typography>
                <Typography variant="body2">
                  Make sure the backend server is running on http://localhost:5001
                </Typography>
              </Alert>
            )}

            {/* Context Badge (for follow-ups) - Story 7.3: Added clear button */}
            {agenticMode && agenticData?.is_followup && (
              <ContextBadge
                previousQuery={agenticData.resolved_query}
                isFollowup={agenticData.is_followup}
                onClear={handleClearConversation}
              />
            )}

            {/* Clarified Query Display */}
            {clarifiedQuery && (
              <Alert
                severity="info"
                sx={{ mb: 2 }}
                onClose={() => setClarifiedQuery(null)}
              >
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
            )}

            {/* Agentic Components (Architecture Section 9.2) */}
            {agenticMode && results && (
              <>
                {/* PRIMARY: Insight Card at TOP */}
                <InsightCard
                  explanation={agenticData?.explanation}
                  keyDetails={agenticData?.key_details}
                  onPin={handlePinInsight}
                  isPinned={isCurrentInsightPinned()}
                />
              </>
            )}

            {/* Results Display */}
            <ResultsDisplay
              loading={loading}
              error={error}
              results={results}
              reflection={agenticMode ? agenticData?.reflection : null}
            />

            {/* Clarification Dialog */}
            <ClarificationDialog
              open={clarificationDialog.open}
              questions={clarificationDialog.questions}
              onSubmit={handleClarificationSubmit}
              onClose={() => setClarificationDialog({ ...clarificationDialog, open: false })}
            />

            {/* Story 7.3: Conversation History Panel */}
            {agenticMode && (
              <ConversationPanel
                open={conversationPanelOpen}
                onClose={() => setConversationPanelOpen(false)}
                history={conversationHistory}
                currentQueryIndex={currentQueryIndex}
                onClearConversation={handleClearConversation}
                onQueryClick={(index) => console.log('Query clicked:', index)}
              />
            )}
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
