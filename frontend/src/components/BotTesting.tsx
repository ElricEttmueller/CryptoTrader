import React, { useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
} from '@mui/material';
import axios from 'axios';

interface BacktestConfig {
  symbol: string;
  startDate: string;
  endDate: string;
  initialBalance: number;
  strategy: string;
  timeframe: string;
  mlConfig: {
    featureWindow: number;
    predictionWindow: number;
    trainSplit: number;
    learningRate: number;
    batchSize: number;
    epochs: number;
  };
}

const BotTesting: React.FC = () => {
  const [config, setConfig] = useState<BacktestConfig>({
    symbol: 'BTC/USD',
    startDate: '2023-01-01',
    endDate: '2023-12-31',
    initialBalance: 10000,
    strategy: 'ml_prediction',
    timeframe: '1h',
    mlConfig: {
      featureWindow: 24,
      predictionWindow: 12,
      trainSplit: 0.8,
      learningRate: 0.001,
      batchSize: 32,
      epochs: 100,
    },
  });

  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleConfigChange = (field: string, value: any) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setConfig({
        ...config,
        [parent]: {
          ...config[parent as keyof BacktestConfig],
          [child]: value,
        },
      });
    } else {
      setConfig({
        ...config,
        [field]: value,
      });
    }
  };

  const runBacktest = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/trading/backtest', {
        symbol: config.symbol,
        start_date: config.startDate,
        end_date: config.endDate,
        initial_balance: config.initialBalance,
        strategy: config.strategy,
        timeframe: config.timeframe,
        ml_config: {
          feature_window: config.mlConfig.featureWindow,
          prediction_window: config.mlConfig.predictionWindow,
          train_split: config.mlConfig.trainSplit,
          learning_rate: config.mlConfig.learningRate,
          batch_size: config.mlConfig.batchSize,
          epochs: config.mlConfig.epochs,
        },
      });
      setResults(response.data);
    } catch (error) {
      console.error('Backtest failed:', error);
    }
    setLoading(false);
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4" gutterBottom>
          Bot Testing Lab
        </Typography>
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Backtest Configuration
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Trading Pair"
                value={config.symbol}
                onChange={(e) => handleConfigChange('symbol', e.target.value)}
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="date"
                label="Start Date"
                value={config.startDate}
                onChange={(e) => handleConfigChange('startDate', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="date"
                label="End Date"
                value={config.endDate}
                onChange={(e) => handleConfigChange('endDate', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="number"
                label="Initial Balance"
                value={config.initialBalance}
                onChange={(e) => handleConfigChange('initialBalance', Number(e.target.value))}
              />
            </Grid>
            
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Strategy</InputLabel>
                <Select
                  value={config.strategy}
                  label="Strategy"
                  onChange={(e) => handleConfigChange('strategy', e.target.value)}
                >
                  <MenuItem value="ml_prediction">ML Prediction</MenuItem>
                  <MenuItem value="mean_reversion">Mean Reversion</MenuItem>
                  <MenuItem value="trend_following">Trend Following</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Timeframe</InputLabel>
                <Select
                  value={config.timeframe}
                  label="Timeframe"
                  onChange={(e) => handleConfigChange('timeframe', e.target.value)}
                >
                  <MenuItem value="1m">1 minute</MenuItem>
                  <MenuItem value="5m">5 minutes</MenuItem>
                  <MenuItem value="15m">15 minutes</MenuItem>
                  <MenuItem value="1h">1 hour</MenuItem>
                  <MenuItem value="4h">4 hours</MenuItem>
                  <MenuItem value="1d">1 day</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>
            ML Configuration
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography gutterBottom>Feature Window</Typography>
              <Slider
                value={config.mlConfig.featureWindow}
                onChange={(e, value) => handleConfigChange('mlConfig.featureWindow', value)}
                min={6}
                max={48}
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography gutterBottom>Prediction Window</Typography>
              <Slider
                value={config.mlConfig.predictionWindow}
                onChange={(e, value) => handleConfigChange('mlConfig.predictionWindow', value)}
                min={1}
                max={24}
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography gutterBottom>Train/Test Split</Typography>
              <Slider
                value={config.mlConfig.trainSplit}
                onChange={(e, value) => handleConfigChange('mlConfig.trainSplit', value)}
                min={0.5}
                max={0.9}
                step={0.1}
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography gutterBottom>Learning Rate</Typography>
              <Slider
                value={config.mlConfig.learningRate}
                onChange={(e, value) => handleConfigChange('mlConfig.learningRate', value)}
                min={0.0001}
                max={0.01}
                step={0.0001}
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Batch Size"
                value={config.mlConfig.batchSize}
                onChange={(e) => handleConfigChange('mlConfig.batchSize', Number(e.target.value))}
              />
            </Grid>
            
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Epochs"
                value={config.mlConfig.epochs}
                onChange={(e) => handleConfigChange('mlConfig.epochs', Number(e.target.value))}
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={runBacktest}
              disabled={loading}
              fullWidth
            >
              {loading ? 'Running Backtest...' : 'Run Backtest'}
            </Button>
          </Box>
        </Paper>
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Backtest Results
          </Typography>
          
          {results && (
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Total Trades
                </Typography>
                <Typography variant="h6">
                  {results.metrics.total_trades}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Win Rate
                </Typography>
                <Typography variant="h6">
                  {(results.metrics.win_rate * 100).toFixed(2)}%
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Total PnL
                </Typography>
                <Typography variant="h6">
                  ${results.metrics.total_pnl.toFixed(2)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Final Portfolio Value
                </Typography>
                <Typography variant="h6">
                  ${results.metrics.final_value.toFixed(2)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Average Win
                </Typography>
                <Typography variant="h6">
                  ${results.metrics.avg_win.toFixed(2)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Average Loss
                </Typography>
                <Typography variant="h6">
                  ${results.metrics.avg_loss.toFixed(2)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Largest Win
                </Typography>
                <Typography variant="h6">
                  ${results.metrics.largest_win.toFixed(2)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">
                  Largest Loss
                </Typography>
                <Typography variant="h6">
                  ${results.metrics.largest_loss.toFixed(2)}
                </Typography>
              </Grid>
            </Grid>
          )}
          
          {!results && !loading && (
            <Typography color="textSecondary">
              Run a backtest to see results
            </Typography>
          )}
          
          {loading && (
            <Typography color="textSecondary">
              Running backtest...
            </Typography>
          )}
        </Paper>
      </Grid>
    </Grid>
  );
};

export default BotTesting;
