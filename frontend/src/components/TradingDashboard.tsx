import React, { useEffect, useState } from 'react';
import { Box, Grid, Paper, Typography, CircularProgress } from '@mui/material';
import axios from 'axios';

interface TradingMetrics {
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  final_value: number;
}

const TradingDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<TradingMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('http://localhost:8000/trading/metrics');
        setMetrics(response.data);
      } catch (error) {
        console.error('Error fetching trading metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (!metrics) {
    return (
      <Box p={2}>
        <Typography color="error">Failed to load trading metrics</Typography>
      </Box>
    );
  }

  const MetricCard = ({ title, value, format = 'number' }: { title: string; value: number; format?: 'number' | 'percentage' | 'currency' }) => {
    const formattedValue = format === 'percentage' 
      ? `${(value * 100).toFixed(2)}%`
      : format === 'currency'
      ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      : value.toLocaleString('en-US');

    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Typography variant="subtitle2" color="textSecondary">
          {title}
        </Typography>
        <Typography variant="h6" sx={{ mt: 1 }}>
          {formattedValue}
        </Typography>
      </Paper>
    );
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" sx={{ mb: 3 }}>Trading Performance</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Total Trades" value={metrics.total_trades} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Win Rate" value={metrics.win_rate} format="percentage" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Total PnL" value={metrics.total_pnl} format="currency" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Final Portfolio Value" value={metrics.final_value} format="currency" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Average Win" value={metrics.avg_win} format="currency" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Average Loss" value={metrics.avg_loss} format="currency" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Largest Win" value={metrics.largest_win} format="currency" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Largest Loss" value={metrics.largest_loss} format="currency" />
        </Grid>
      </Grid>
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Trading Visualizations</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '400px' }}>
              <iframe
                src="http://localhost:8000/trading/viz/performance"
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="Trading Performance"
              />
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '400px' }}>
              <iframe
                src="http://localhost:8000/trading/viz/pnl"
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="PnL Distribution"
              />
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '400px' }}>
              <iframe
                src="http://localhost:8000/trading/viz/signals"
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="Trading Signals"
              />
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '400px' }}>
              <iframe
                src="http://localhost:8000/trading/viz/ml"
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="ML Metrics"
              />
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default TradingDashboard;
