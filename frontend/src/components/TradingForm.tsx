import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import axios from 'axios';
import { useTradingContext } from '../context/TradingContext';

interface TradingFormProps {
}

type OrderType = 'market' | 'limit';
type OrderSide = 'buy' | 'sell';

const TradingForm: React.FC<TradingFormProps> = () => {
  const { selectedPair, marketData } = useTradingContext();
  const currentPrice = marketData?.currentPrice ?? 0;

  const [orderType, setOrderType] = useState<OrderType>('market');
  const [orderSide, setOrderSide] = useState<OrderSide>('buy');
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>(currentPrice.toString());
  const [total, setTotal] = useState<string>('');

  const handleOrderTypeChange = (event: SelectChangeEvent) => {
    setOrderType(event.target.value as OrderType);
    if (event.target.value === 'market') {
      setPrice(currentPrice.toString());
    }
  };

  const handleOrderSideChange = (
    _event: React.MouseEvent<HTMLElement>,
    newOrderSide: OrderSide,
  ) => {
    if (newOrderSide !== null) {
      setOrderSide(newOrderSide);
    }
  };

  const handleAmountChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newAmount = event.target.value;
    setAmount(newAmount);
    if (price) {
      setTotal((parseFloat(newAmount) * parseFloat(price)).toString());
    }
  };

  const handlePriceChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newPrice = event.target.value;
    setPrice(newPrice);
    if (amount) {
      setTotal((parseFloat(amount) * parseFloat(newPrice)).toString());
    }
  };

  const handleTotalChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newTotal = event.target.value;
    setTotal(newTotal);
    if (price && parseFloat(price) !== 0) {
      setAmount((parseFloat(newTotal) / parseFloat(price)).toString());
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const order = {
        type: orderType,
        side: orderSide,
        amount: parseFloat(amount),
        price: orderType === 'limit' ? parseFloat(price) : undefined,
        symbol: selectedPair,
      };

      await axios.post('http://localhost:8000/place-order', order);
      // Reset form or show success message
    } catch (error) {
      console.error('Error placing order:', error);
      // Show error message to user
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Place Order
      </Typography>

      <Box sx={{ mb: 2 }}>
        <ToggleButtonGroup
          value={orderSide}
          exclusive
          onChange={handleOrderSideChange}
          fullWidth
        >
          <ToggleButton
            value="buy"
            sx={{
              '&.Mui-selected': {
                backgroundColor: 'success.main',
                color: 'white',
                '&:hover': {
                  backgroundColor: 'success.dark',
                },
              },
            }}
          >
            Buy
          </ToggleButton>
          <ToggleButton
            value="sell"
            sx={{
              '&.Mui-selected': {
                backgroundColor: 'error.main',
                color: 'white',
                '&:hover': {
                  backgroundColor: 'error.dark',
                },
              },
            }}
          >
            Sell
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Order Type</InputLabel>
        <Select
          value={orderType}
          label="Order Type"
          onChange={handleOrderTypeChange}
        >
          <MenuItem value="market">Market</MenuItem>
          <MenuItem value="limit">Limit</MenuItem>
        </Select>
      </FormControl>

      <TextField
        fullWidth
        label="Amount (BTC)"
        type="number"
        value={amount}
        onChange={handleAmountChange}
        sx={{ mb: 2 }}
        InputProps={{
          inputProps: { min: 0, step: 0.0001 },
        }}
      />

      <TextField
        fullWidth
        label="Price (USDT)"
        type="number"
        value={price}
        onChange={handlePriceChange}
        sx={{ mb: 2 }}
        disabled={orderType === 'market'}
        InputProps={{
          inputProps: { min: 0, step: 0.01 },
        }}
      />

      <TextField
        fullWidth
        label="Total (USDT)"
        type="number"
        value={total}
        onChange={handleTotalChange}
        sx={{ mb: 2 }}
        InputProps={{
          inputProps: { min: 0, step: 0.01 },
        }}
      />

      <Button
        type="submit"
        variant="contained"
        fullWidth
        color={orderSide === 'buy' ? 'success' : 'error'}
        sx={{ mt: 2 }}
      >
        {orderSide === 'buy' ? 'Buy' : 'Sell'} BTC
      </Button>
    </Box>
  );
};

export default TradingForm;
