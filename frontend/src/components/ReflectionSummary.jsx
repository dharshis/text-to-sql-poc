/**
 * ReflectionSummary Component
 * Architecture Reference: Section 9.2 (Component Specifications)
 * 
 * Displays reflection results and quality checks.
 */

import React, { useState } from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';

const ReflectionSummary = ({ reflection }) => {
  if (!reflection) {
    return null;
  }

  const { is_acceptable, critical_errors = [], issues = [] } = reflection;
  const allIssues = [...critical_errors, ...issues];

  return (
    <Accordion
      defaultExpanded={false}
      sx={{ mb: 2 }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box display="flex" alignItems="center" gap={1}>
          {is_acceptable ? (
            <>
              <CheckCircleIcon color="success" />
              <Typography>Quality Check: Passed</Typography>
              <Chip label="Acceptable" color="success" size="small" />
            </>
          ) : (
            <>
              <WarningIcon color="warning" />
              <Typography>Quality Check: Issues Found</Typography>
              <Chip label="Retrying" color="warning" size="small" />
            </>
          )}
        </Box>
      </AccordionSummary>

      <AccordionDetails>
        {allIssues.length > 0 ? (
          <>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Issues detected:
            </Typography>
            <List dense>
              {allIssues.map((issue, index) => (
                <ListItem key={index}>
                  <ListItemText primary={`• ${issue}`} />
                </ListItem>
              ))}
            </List>
          </>
        ) : (
          <Typography variant="body2" color="success.main">
            ✅ SQL quality is acceptable. No critical issues found.
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
};

export default ReflectionSummary;

