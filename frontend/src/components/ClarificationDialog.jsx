/**
 * ClarificationDialog Component
 * Architecture Reference: Section 9.2 (Component Specifications)
 * 
 * Displays clarification questions from the agent when ambiguity is detected.
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const ClarificationDialog = ({ open, questions, onSubmit, onClose }) => {
  const [response, setResponse] = useState('');

  const handleSubmit = () => {
    if (response.trim()) {
      onSubmit(response);
      setResponse('');
    }
  };

  const handleClose = () => {
    setResponse('');
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <HelpOutlineIcon color="info" />
          <Typography variant="h6">Need More Information</Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Your query is a bit ambiguous. Please provide more details:
        </Typography>

        {questions && questions.length > 0 && (
          <List dense>
            {questions.map((question, index) => (
              <ListItem key={index} disableGutters>
                <ListItemText
                  primary={`${index + 1}. ${question}`}
                  primaryTypographyProps={{ fontWeight: 500 }}
                />
              </ListItem>
            ))}
          </List>
        )}

        <TextField
          fullWidth
          multiline
          rows={3}
          label="Your response"
          variant="outlined"
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          sx={{ mt: 2 }}
          placeholder="Please provide additional details..."
          autoFocus
        />
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} color="secondary">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          disabled={!response.trim()}
        >
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ClarificationDialog;

