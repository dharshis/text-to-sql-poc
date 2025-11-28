/**
 * IterationIndicator Component
 * Architecture Reference: Section 9.2 (Component Specifications)
 * 
 * Shows iteration count for agent workflow.
 */

import React from 'react';
import { Chip } from '@mui/material';
import LoopIcon from '@mui/icons-material/Loop';

const IterationIndicator = ({ iteration, maxIterations }) => {
  if (!iteration || iteration <= 1) {
    return null;
  }

  const isComplete = iteration >= maxIterations;
  const color = isComplete ? 'success' : 'primary';

  return (
    <Chip
      icon={<LoopIcon />}
      label={`Attempt ${iteration}/${maxIterations}`}
      color={color}
      size="small"
      sx={{ ml: 1 }}
    />
  );
};

export default IterationIndicator;

