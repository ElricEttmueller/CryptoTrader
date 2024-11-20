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

function OrderBook() {
  // Mock data - will be replaced with real data from the API
  const asks = [
    { price: 45000.50, amount: 0.5 },
    { price: 45001.00, amount: 1.2 },
    { price: 45001.50, amount: 0.8 },
  ];

  const bids = [
    { price: 44999.50, amount: 0.7 },
    { price: 44999.00, amount: 1.5 },
    { price: 44998.50, amount: 0.3 },
  ];

  return (
    <Box>
      <Typography variant="h6" component="h2" gutterBottom>
        Order Book
      </Typography>
      
      {/* Asks (Sell Orders) */}
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Price (USDT)</TableCell>
              <TableCell align="right">Amount (BTC)</TableCell>
              <TableCell align="right">Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {asks.map((order, index) => (
              <TableRow key={index} sx={{ color: '#ff4444' }}>
                <TableCell component="th" scope="row" sx={{ color: '#ff4444' }}>
                  {order.price.toFixed(2)}
                </TableCell>
                <TableCell align="right">{order.amount.toFixed(4)}</TableCell>
                <TableCell align="right">
                  {(order.price * order.amount).toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Current Price */}
      <Box sx={{ my: 2, textAlign: 'center' }}>
        <Typography variant="h6" component="div" sx={{ color: '#90caf9' }}>
          45000.00 USDT
        </Typography>
      </Box>

      {/* Bids (Buy Orders) */}
      <TableContainer>
        <Table size="small">
          <TableBody>
            {bids.map((order, index) => (
              <TableRow key={index}>
                <TableCell component="th" scope="row" sx={{ color: '#4caf50' }}>
                  {order.price.toFixed(2)}
                </TableCell>
                <TableCell align="right">{order.amount.toFixed(4)}</TableCell>
                <TableCell align="right">
                  {(order.price * order.amount).toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default OrderBook;
