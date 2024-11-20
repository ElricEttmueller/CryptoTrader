import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Grid, Paper } from '@mui/material';
import TradingView from './components/TradingView';
import OrderBook from './components/OrderBook';
import TradingForm from './components/TradingForm';
import TradeHistory from './components/TradeHistory';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, p: 3, height: '100vh', backgroundColor: 'background.default' }}>
        <Grid container spacing={2} sx={{ height: 'calc(100% - 24px)' }}>
          {/* Left column - Chart */}
          <Grid item xs={12} md={8} sx={{ height: '100%' }}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <TradingView />
            </Paper>
          </Grid>

          {/* Right column - Trading Form, Order Book, Trade History */}
          <Grid item xs={12} md={4} sx={{ height: '100%' }}>
            <Grid container spacing={2} sx={{ height: '100%' }}>
              {/* Trading Form */}
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <TradingForm />
                </Paper>
              </Grid>

              {/* Order Book */}
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <OrderBook />
                </Paper>
              </Grid>

              {/* Trade History */}
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <TradeHistory />
                </Paper>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Box>
    </ThemeProvider>
  );
}

export default App;
