/**
 * ConversationHeader Component
 *
 * Sticky header bar containing:
 * - Application title and ClientSelector
 * - Health status indicator
 * - Agentic mode toggle
 * - New Conversation button
 */

import React from 'react';
import {
  Box,
  Typography,
  Button,
  Chip,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon, AddComment } from '@mui/icons-material';
import ClientSelector from './ClientSelector';

const ConversationHeader = ({
  clients,
  selectedClientId,
  onClientChange,
  clientsLoading,
  healthStatus,
  agenticMode,
  onAgenticModeChange,
  onNewConversation,
  conversationCount,
}) => {
  return (
    <Box
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: 1100,
        backgroundColor: 'background.paper',
        borderBottom: '1px solid',
        borderColor: 'divider',
        height: '80px',
        px: 3,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: 1,
      }}
    >
      {/* Left Section: Title + Client Selector */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            color: 'primary.main',
            minWidth: '220px',
          }}
        >
          Smart Insight Generator
        </Typography>

        <ClientSelector
          clients={clients}
          selectedClientId={selectedClientId}
          onClientChange={onClientChange}
          loading={clientsLoading}
        />
      </Box>

      {/* Right Section: Health Status + Mode Toggle + New Conversation Button */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* Health Status */}
        {healthStatus && (
          <Chip
            icon={healthStatus.status === 'healthy' ? <CheckCircle /> : <ErrorIcon />}
            label={healthStatus.status === 'healthy' ? 'Backend Connected' : 'Backend Error'}
            color={healthStatus.status === 'healthy' ? 'success' : 'error'}
            size="small"
            variant="outlined"
          />
        )}

        {/* Agentic Mode Toggle */}
        <FormControlLabel
          control={
            <Switch
              checked={agenticMode}
              onChange={(e) => onAgenticModeChange(e.target.checked)}
              color="primary"
            />
          }
          label="Agentic Mode"
          sx={{ mr: 1 }}
        />

        {/* New Conversation Button */}
        <Button
          variant="outlined"
          color="primary"
          onClick={onNewConversation}
          startIcon={<AddComment />}
          sx={{
            height: 40,
            fontWeight: 600,
          }}
        >
          New Conversation
          {conversationCount > 0 && ` (${conversationCount})`}
        </Button>
      </Box>
    </Box>
  );
};

export default ConversationHeader;
