import React from 'react';
import { Grid, Paper, Box } from '@mui/material';
import TradingView from './TradingView';
import OrderForm from './OrderForm';
import OrderBook from './OrderBook';
import TradeHistory from './TradeHistory';

const LiveTrading: React.FC = () => {
  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Grid container spacing={3}>
        {/* Trading Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '600px' }}>
            <TradingView />
          </Paper>
        </Grid>

        {/* Order Form */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '600px', overflow: 'auto' }}>
            <OrderForm />
          </Paper>
        </Grid>

        {/* Order Book */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <OrderBook />
          </Paper>
        </Grid>

        {/* Trade History */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <TradeHistory />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default LiveTrading;
