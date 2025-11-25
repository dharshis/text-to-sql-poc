/**
 * ValidationMetrics component - Security validation display.
 *
 * Shows validation checks with color-coded indicators:
 * - Green (PASS) - Check passed
 * - Red (FAIL) - Check failed
 * - Yellow (WARNING) - Warning message
 */

import React from 'react';
import {
  Paper,
  Typography,
  Box,
  Chip,
  Alert,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

const ValidationMetrics = ({ validation }) => {
  if (!validation) {
    return null;
  }

  const { passed, checks, warnings } = validation;

  // Get status icon and color
  const getStatusIcon = (status) => {
    switch (status) {
      case 'PASS':
        return <CheckIcon fontSize="small" />;
      case 'FAIL':
        return <ErrorIcon fontSize="small" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'PASS':
        return 'success';
      case 'FAIL':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <SecurityIcon color="primary" />
        <Typography variant="h6">Security Validation</Typography>
      </Box>

      {/* Overall Status */}
      <Alert
        severity={passed ? 'success' : 'error'}
        sx={{ mb: 2 }}
        icon={passed ? <CheckIcon /> : <ErrorIcon />}
      >
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          {passed
            ? 'Validation Passed - Query meets security requirements'
            : 'Validation Failed - Query does not meet security requirements'}
        </Typography>
      </Alert>

      {/* Validation Checks */}
      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2, mb: 1 }}>
        Security Checks:
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
        {checks && checks.map((check, index) => (
          <Chip
            key={index}
            icon={getStatusIcon(check.status)}
            label={`${check.name}: ${check.status}`}
            color={getStatusColor(check.status)}
            variant={check.status === 'PASS' ? 'filled' : 'outlined'}
            sx={{ fontWeight: 500 }}
          />
        ))}
      </Box>

      {/* Failed Checks Details */}
      {checks && checks.some((c) => c.status === 'FAIL') && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" gutterBottom sx={{ color: 'error.main' }}>
            Failed Checks:
          </Typography>
          <Box sx={{ pl: 2 }}>
            {checks
              .filter((c) => c.status === 'FAIL')
              .map((check, index) => (
                <Box key={index} sx={{ mb: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    • {check.name}
                  </Typography>
                  {check.message && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ pl: 2 }}
                    >
                      {check.message}
                    </Typography>
                  )}
                </Box>
              ))}
          </Box>
        </>
      )}

      {/* Warnings */}
      {warnings && warnings.length > 0 && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <WarningIcon fontSize="small" color="warning" />
            Warnings:
          </Typography>
          <Box sx={{ pl: 2 }}>
            {warnings.map((warning, index) => (
              <Box key={index} sx={{ mb: 1 }}>
                <Typography variant="body2" color="warning.main">
                  • {warning.message || warning}
                </Typography>
              </Box>
            ))}
          </Box>
        </>
      )}

      {/* Validation Metrics */}
      {validation.execution_time !== undefined && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mt: 2 }}
        >
          Validation completed in {validation.execution_time}s
        </Typography>
      )}
    </Paper>
  );
};

export default ValidationMetrics;
