import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
} from '@mui/material';

function TradeHistory() {
  // Mock data - will be replaced with real data from the API
  const trades = [
    {
      time: '14:30:45',
      price: 45000.50,
      amount: 0.5,
      side: 'buy',
    },
    {
      time: '14:30:30',
      price: 45001.00,
      amount: 1.2,
      side: 'sell',
    },
    {
      time: '14:30:15',
      price: 44999.50,
      amount: 0.8,
      side: 'buy',
    },
  ];

  return (
    <Box>
      <Typography variant="h6" component="h2" gutterBottom>
        Trade History
      </Typography>
      
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Price</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell align="right">Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {trades.map((trade, index) => (
              <TableRow key={index}>
                <TableCell>{trade.time}</TableCell>
                <TableCell
                  sx={{
                    color: trade.side === 'buy' ? '#4caf50' : '#ff4444',
                  }}
                >
                  {trade.price.toFixed(2)}
                </TableCell>
                <TableCell align="right">{trade.amount.toFixed(4)}</TableCell>
                <TableCell align="right">
                  {(trade.price * trade.amount).toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default TradeHistory;
