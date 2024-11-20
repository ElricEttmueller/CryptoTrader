import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Slider,
  Grid,
} from '@mui/material';

function TradingForm() {
  const [orderType, setOrderType] = useState('limit');
  const [side, setSide] = useState('buy');
  const [price, setPrice] = useState('');
  const [amount, setAmount] = useState('');
  const [total, setTotal] = useState('');
  const [sliderValue, setSliderValue] = useState(0);

  const handleOrderTypeChange = (event, newOrderType) => {
    if (newOrderType !== null) {
      setOrderType(newOrderType);
    }
  };

  const handleSideChange = (event, newSide) => {
    if (newSide !== null) {
      setSide(newSide);
    }
  };

  const handleSliderChange = (event, newValue) => {
    setSliderValue(newValue);
    // Calculate amount based on slider value
    // This is just an example - you'll need to implement your own logic
    setAmount((newValue * 0.01).toFixed(8));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    // TODO: Implement order submission
    console.log({
      orderType,
      side,
      price,
      amount,
      total,
    });
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Typography variant="h6" gutterBottom>
        Place Order
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <ToggleButtonGroup
            value={orderType}
            exclusive
            onChange={handleOrderTypeChange}
            fullWidth
          >
            <ToggleButton value="limit">Limit</ToggleButton>
            <ToggleButton value="market">Market</ToggleButton>
            <ToggleButton value="stop">Stop Limit</ToggleButton>
          </ToggleButtonGroup>
        </Grid>

        <Grid item xs={12}>
          <ToggleButtonGroup
            value={side}
            exclusive
            onChange={handleSideChange}
            fullWidth
          >
            <ToggleButton
              value="buy"
              sx={{ color: '#4caf50', '&.Mui-selected': { color: '#4caf50' } }}
            >
              Buy
            </ToggleButton>
            <ToggleButton
              value="sell"
              sx={{ color: '#ff4444', '&.Mui-selected': { color: '#ff4444' } }}
            >
              Sell
            </ToggleButton>
          </ToggleButtonGroup>
        </Grid>

        <Grid item xs={12}>
          <TextField
            label="Price"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            fullWidth
            type="number"
            InputProps={{
              endAdornment: <Typography>USDT</Typography>,
            }}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            label="Amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            fullWidth
            type="number"
            InputProps={{
              endAdornment: <Typography>BTC</Typography>,
            }}
          />
        </Grid>

        <Grid item xs={12}>
          <Typography gutterBottom>Amount (%)</Typography>
          <Slider
            value={sliderValue}
            onChange={handleSliderChange}
            marks={[
              { value: 0, label: '0%' },
              { value: 25, label: '25%' },
              { value: 50, label: '50%' },
              { value: 75, label: '75%' },
              { value: 100, label: '100%' },
            ]}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            label="Total"
            value={total}
            onChange={(e) => setTotal(e.target.value)}
            fullWidth
            type="number"
            InputProps={{
              endAdornment: <Typography>USDT</Typography>,
            }}
          />
        </Grid>

        <Grid item xs={12}>
          <Button
            type="submit"
            variant="contained"
            fullWidth
            sx={{
              bgcolor: side === 'buy' ? '#4caf50' : '#ff4444',
              '&:hover': {
                bgcolor: side === 'buy' ? '#45a049' : '#ff3333',
              },
            }}
          >
            {side === 'buy' ? 'Buy BTC' : 'Sell BTC'}
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
}

export default TradingForm;
