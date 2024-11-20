import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container, Tabs, Tab, Box } from '@mui/material';
import { styled } from '@mui/material/styles';
import LiveTrading from './components/LiveTrading';
import PerformanceDashboard from './components/PerformanceDashboard';
import BotTesting from './components/BotTesting';

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  background: theme.palette.background.paper,
  boxShadow: 'none',
  borderBottom: `1px solid ${theme.palette.divider}`,
}));

const StyledTab = styled(Tab)(({ theme }) => ({
  color: theme.palette.text.primary,
  '&.Mui-selected': {
    color: theme.palette.primary.main,
  },
}));

// Navigation component to handle tab state
const Navigation = () => {
  const location = useLocation();
  
  // Map routes to tab values
  const pathToTabValue: { [key: string]: number } = {
    '/': 0,
    '/dashboard': 1,
    '/testing': 2,
  };

  return (
    <Tabs value={pathToTabValue[location.pathname] ?? 0} textColor="inherit">
      <StyledTab label="Live Trading" component={Link} to="/" />
      <StyledTab label="Performance Dashboard" component={Link} to="/dashboard" />
      <StyledTab label="Bot Testing Lab" component={Link} to="/testing" />
    </Tabs>
  );
};

function App() {
  return (
    <Router>
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        minHeight: '100vh',
        bgcolor: 'background.default',
        color: 'text.primary'
      }}>
        <StyledAppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              CryptoTrader
            </Typography>
            <Navigation />
          </Toolbar>
        </StyledAppBar>
        
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flex: 1 }}>
          <Routes>
            <Route path="/" element={<LiveTrading />} />
            <Route path="/dashboard" element={<PerformanceDashboard />} />
            <Route path="/testing" element={<BotTesting />} />
          </Routes>
        </Container>
      </Box>
    </Router>
  );
}

export default App;
