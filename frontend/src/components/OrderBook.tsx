import React, { useEffect, useState } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import axios from 'axios';

interface OrderBookData {
  bids: [number, number][];
  asks: [number, number][];
}

const OrderBook: React.FC = () => {
  const [orderBook, setOrderBook] = useState<OrderBookData | null>(null);

  useEffect(() => {
    const fetchOrderBook = async () => {
      try {
        const response = await axios.get('http://localhost:8000/orderbook/BTC-USDT');
        setOrderBook(response.data);
      } catch (error) {
        console.error('Error fetching order book:', error);
      }
    };

    fetchOrderBook();
    const interval = setInterval(fetchOrderBook, 1000); // Update every second

    return () => clearInterval(interval);
  }, []);

  const formatNumber = (num: number) => {
    return num.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Order Book
      </Typography>

      <TableContainer sx={{ maxHeight: 400 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Price (USDT)</TableCell>
              <TableCell align="right">Amount (BTC)</TableCell>
              <TableCell align="right">Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {/* Asks (Sell Orders) - Displayed in reverse order */}
            {orderBook?.asks.slice(0, 10).reverse().map(([price, amount]) => (
              <TableRow key={`ask-${price}`}>
                <TableCell sx={{ color: 'error.main' }}>
                  {formatNumber(price)}
                </TableCell>
                <TableCell align="right">{amount.toFixed(6)}</TableCell>
                <TableCell align="right">{formatNumber(price * amount)}</TableCell>
              </TableRow>
            ))}

            {/* Spread */}
            {orderBook && (
              <TableRow>
                <TableCell colSpan={3} align="center" sx={{ py: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Spread: {formatNumber(orderBook.asks[0][0] - orderBook.bids[0][0])} USDT (
                    {((orderBook.asks[0][0] - orderBook.bids[0][0]) / orderBook.bids[0][0] * 100).toFixed(2)}%)
                  </Typography>
                </TableCell>
              </TableRow>
            )}

            {/* Bids (Buy Orders) */}
            {orderBook?.bids.slice(0, 10).map(([price, amount]) => (
              <TableRow key={`bid-${price}`}>
                <TableCell sx={{ color: 'success.main' }}>
                  {formatNumber(price)}
                </TableCell>
                <TableCell align="right">{amount.toFixed(6)}</TableCell>
                <TableCell align="right">{formatNumber(price * amount)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default OrderBook;
