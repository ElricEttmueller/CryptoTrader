import React from 'react';
import { Box, Typography } from '@mui/material';

const TradingChart: React.FC = () => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Price Chart
      </Typography>
      {/* TradingView chart will be integrated here */}
      <Box
        sx={{
          height: '400px',
          bgcolor: 'background.paper',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography color="textSecondary">
          Trading chart will be displayed here
        </Typography>
      </Box>
    </Box>
  );
};

export default TradingChart;
