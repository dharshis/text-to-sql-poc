/**
 * ValidationSummary Component
 *
 * Unified component that displays both Quality Check and Security Validation
 * with clear distinction and consistent design.
 */

import React, { useState } from 'react';
import {
  Paper,
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
  Alert,
  List,
  ListItem,
  ListItemText,
  Stack,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Security as SecurityIcon,
  Psychology as PsychologyIcon,
  VerifiedUser as VerifiedUserIcon,
} from '@mui/icons-material';

const ValidationSummary = ({ reflection, securityValidation }) => {
  const [qualityExpanded, setQualityExpanded] = useState(false);
  const [securityExpanded, setSecurityExpanded] = useState(false);

  // Don't render if both are empty
  if (!reflection && !securityValidation) {
    return null;
  }

  // Parse reflection data
  const criticalErrors = Array.isArray(reflection?.critical_errors) ? reflection.critical_errors : [];
  const issues = Array.isArray(reflection?.issues) ? reflection.issues : [];
  const allQualityIssues = [...criticalErrors, ...issues].filter(issue => issue && issue.trim && issue.trim() !== '');
  const hasQualityIssues = allQualityIssues.length > 0;

  // Debug logging
  console.log('ValidationSummary - reflection:', reflection);
  console.log('ValidationSummary - criticalErrors:', criticalErrors);
  console.log('ValidationSummary - issues:', issues);
  console.log('ValidationSummary - allQualityIssues:', allQualityIssues);
  console.log('ValidationSummary - hasQualityIssues:', hasQualityIssues);

  // Parse security validation data
  const securityPassed = securityValidation?.passed ?? true;
  const securityChecks = securityValidation?.checks || [];
  const securityWarnings = securityValidation?.warnings || [];
  const failedChecks = securityChecks.filter((c) => c.status === 'FAIL');

  // Overall status - passed if no quality issues AND security passed
  const overallPassed = !hasQualityIssues && securityPassed;

  return (
    <Paper
      sx={{
        width: '100%',
        maxWidth: '100%',
        overflow: 'hidden',
        boxSizing: 'border-box',
        borderRadius: 3,
      }}
    >
      {/* Header */}
      <Box sx={{ p: 3, pb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <VerifiedUserIcon
            sx={{
              fontSize: 28,
              color: overallPassed ? 'success.main' : 'error.main'
            }}
          />
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Validation Summary
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Quality checks and security validation results
            </Typography>
          </Box>
          <Chip
            icon={overallPassed ? <CheckCircleIcon /> : <ErrorIcon />}
            label={overallPassed ? 'All Checks Passed' : 'Issues Detected'}
            color={overallPassed ? 'success' : 'error'}
            sx={{ fontWeight: 600 }}
          />
        </Box>

        {/* Overall Status Alert */}
        <Alert
          severity={overallPassed ? 'success' : 'warning'}
          icon={overallPassed ? <CheckCircleIcon /> : <WarningIcon />}
          sx={{ borderRadius: 2 }}
        >
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {overallPassed
              ? 'Query passed all quality and security validations'
              : 'Review the validation details below for improvements'}
          </Typography>
        </Alert>
      </Box>

      {/* Quality Check Section - Always show, but only expandable if there are issues */}
      {reflection && (
        <>
          <Divider />
          <Accordion
            expanded={hasQualityIssues && qualityExpanded}
            onChange={hasQualityIssues ? () => setQualityExpanded(!qualityExpanded) : undefined}
            disabled={!hasQualityIssues}
            sx={{
              boxShadow: 'none',
              '&:before': { display: 'none' },
              backgroundColor: 'transparent',
              '&.Mui-disabled': {
                backgroundColor: 'transparent',
              },
            }}
          >
            <AccordionSummary
              expandIcon={hasQualityIssues ? <ExpandMoreIcon /> : null}
              sx={{
                px: 3,
                py: 1.5,
                cursor: hasQualityIssues ? 'pointer' : 'default',
                '&:hover': {
                  backgroundColor: hasQualityIssues ? 'action.hover' : 'transparent',
                },
                '&.Mui-disabled': {
                  opacity: 1,
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <PsychologyIcon
                  sx={{
                    fontSize: 24,
                    color: hasQualityIssues ? 'warning.main' : 'success.main'
                  }}
                />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    Quality Check
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    AI-powered query quality assessment
                  </Typography>
                </Box>
                <Stack direction="row" spacing={1} sx={{ minWidth: 120, justifyContent: 'flex-end' }}>
                  {hasQualityIssues ? (
                    <Chip
                      icon={<WarningIcon />}
                      label={`${allQualityIssues.length} Issue${allQualityIssues.length !== 1 ? 's' : ''}`}
                      size="small"
                      color="warning"
                      variant="outlined"
                    />
                  ) : (
                    <Chip
                      icon={<CheckCircleIcon />}
                      label="Passed"
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  )}
                </Stack>
              </Box>
            </AccordionSummary>

            {hasQualityIssues && (
              <AccordionDetails sx={{ px: 3, py: 2, backgroundColor: 'background.accent' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 2 }}>
                    The following quality issues were detected:
                  </Typography>
                  <List dense sx={{ p: 0 }}>
                    {allQualityIssues.map((issue, index) => (
                      <ListItem
                        key={index}
                        sx={{
                          px: 2,
                          py: 1,
                          mb: 1,
                          borderRadius: 2,
                          backgroundColor: 'background.paper',
                          border: '1px solid',
                          borderColor: 'divider',
                        }}
                      >
                        <WarningIcon
                          sx={{
                            fontSize: 18,
                            color: 'warning.main',
                            mr: 1.5
                          }}
                        />
                        <ListItemText
                          primary={issue}
                          primaryTypographyProps={{
                            variant: 'body2',
                            color: 'text.primary',
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              </AccordionDetails>
            )}
          </Accordion>
        </>
      )}

      {/* Security Validation Section */}
      {securityValidation && (
        <>
          <Divider />
          <Accordion
          expanded={securityExpanded}
          onChange={() => setSecurityExpanded(!securityExpanded)}
          sx={{
            boxShadow: 'none',
            '&:before': { display: 'none' },
            backgroundColor: 'transparent',
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              px: 3,
              py: 1.5,
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              <SecurityIcon
                sx={{
                  fontSize: 24,
                  color: securityPassed ? 'success.main' : 'error.main'
                }}
              />
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Security Validation
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  SQL injection and security checks
                </Typography>
              </Box>
              <Stack direction="row" spacing={1} sx={{ minWidth: 120, justifyContent: 'flex-end' }}>
                {securityPassed ? (
                  <Chip
                    icon={<CheckCircleIcon />}
                    label="Secure"
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                ) : (
                  <Chip
                    icon={<ErrorIcon />}
                    label={`${failedChecks.length} Failed`}
                    size="small"
                    color="error"
                    variant="outlined"
                  />
                )}
                {securityWarnings.length > 0 && (
                  <Chip
                    icon={<WarningIcon />}
                    label={`${securityWarnings.length} Warning${securityWarnings.length !== 1 ? 's' : ''}`}
                    size="small"
                    color="warning"
                    variant="outlined"
                  />
                )}
              </Stack>
            </Box>
          </AccordionSummary>

          <AccordionDetails sx={{ px: 3, py: 2, backgroundColor: 'background.accent' }}>
            {/* Security Checks */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
                Security Checks
              </Typography>
              <Stack spacing={1}>
                {securityChecks.map((check, index) => {
                  const isPassed = check.status === 'PASS';
                  const isFailed = check.status === 'FAIL';

                  return (
                    <Box
                      key={index}
                      sx={{
                        px: 2,
                        py: 1.5,
                        borderRadius: 2,
                        backgroundColor: 'background.paper',
                        border: '1.5px solid',
                        borderColor: isPassed
                          ? 'success.light'
                          : isFailed
                            ? 'error.light'
                            : 'divider',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: 1.5,
                      }}
                    >
                      {isPassed ? (
                        <CheckCircleIcon sx={{ fontSize: 20, color: 'success.main', mt: 0.25 }} />
                      ) : (
                        <ErrorIcon sx={{ fontSize: 20, color: 'error.main', mt: 0.25 }} />
                      )}
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                          {check.name}
                        </Typography>
                        {check.message && (
                          <Typography variant="caption" color="text.secondary">
                            {check.message}
                          </Typography>
                        )}
                      </Box>
                      <Chip
                        label={check.status}
                        size="small"
                        color={isPassed ? 'success' : 'error'}
                        sx={{
                          fontWeight: 600,
                          fontSize: '0.7rem',
                          height: 24,
                        }}
                      />
                    </Box>
                  );
                })}
              </Stack>
            </Box>

            {/* Warnings Section */}
            {securityWarnings.length > 0 && (
              <Box>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
                  <WarningIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                  Warnings
                </Typography>
                <List dense sx={{ p: 0 }}>
                  {securityWarnings.map((warning, index) => (
                    <ListItem
                      key={index}
                      sx={{
                        px: 2,
                        py: 1,
                        mb: 1,
                        borderRadius: 2,
                        backgroundColor: 'background.paper',
                        border: '1px solid',
                        borderColor: 'warning.light',
                      }}
                    >
                      <WarningIcon
                        sx={{
                          fontSize: 18,
                          color: 'warning.main',
                          mr: 1.5
                        }}
                      />
                      <ListItemText
                        primary={warning.message || warning}
                        primaryTypographyProps={{
                          variant: 'body2',
                          color: 'text.primary',
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {/* All Passed State */}
            {securityPassed && securityWarnings.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 2 }}>
                <SecurityIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                <Typography variant="body2" color="success.main" sx={{ fontWeight: 500 }}>
                  All security checks passed. Query is secure.
                </Typography>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
        </>
      )}
    </Paper>
  );
};

export default ValidationSummary;
