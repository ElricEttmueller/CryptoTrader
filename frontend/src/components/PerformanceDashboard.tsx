import React from 'react';
import { Grid, Paper, Typography } from '@mui/material';

const PerformanceDashboard: React.FC = () => {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4" gutterBottom>
          Performance Dashboard
        </Typography>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2, height: '300px' }}>
          <Typography variant="h6" gutterBottom>
            Portfolio Performance
          </Typography>
        </Paper>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2, height: '300px' }}>
          <Typography variant="h6" gutterBottom>
            Trading History
          </Typography>
        </Paper>
      </Grid>
      
      <Grid item xs={12}>
        <Paper sx={{ p: 2, height: '400px' }}>
          <Typography variant="h6" gutterBottom>
            Performance Metrics
          </Typography>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default PerformanceDashboard;
