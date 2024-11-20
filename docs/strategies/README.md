# Trading Strategies Documentation

## Overview
CryptoTrader supports multiple trading strategies through a flexible and extensible strategy framework. Each strategy inherits from the `BaseStrategy` class and implements specific trading logic while maintaining a consistent interface.

## Available Strategies

### 1. Mean Reversion Strategy
A statistical arbitrage strategy that trades on the assumption that prices will revert to their historical mean.

```python
from strategies import MeanReversionStrategy

config = {
    'window_size': 20,
    'std_dev_threshold': 2.0,
    'position_size': 0.1
}
strategy = MeanReversionStrategy('mean_rev_1', config)
```

Key Parameters:
- `window_size`: Period for calculating moving average (default: 20)
- `std_dev_threshold`: Number of standard deviations for entry/exit (default: 2.0)
- `position_size`: Maximum position size as fraction of portfolio (default: 0.1)

### 2. Trend Following Strategy
A momentum-based strategy that uses moving average crossovers and RSI for trend detection.

```python
from strategies import TrendFollowingStrategy

config = {
    'fast_ma_period': 10,
    'slow_ma_period': 30,
    'rsi_period': 14,
    'position_size': 0.1
}
strategy = TrendFollowingStrategy('trend_1', config)
```

Key Parameters:
- `fast_ma_period`: Period for fast moving average (default: 10)
- `slow_ma_period`: Period for slow moving average (default: 30)
- `rsi_period`: Period for RSI calculation (default: 14)
- `position_size`: Maximum position size as fraction of portfolio (default: 0.1)

### 3. Moving Average Strategy
Simple moving average crossover strategy.

```python
from strategies import MovingAverageStrategy

config = {
    'ma_period': 20,
    'position_size': 0.1
}
strategy = MovingAverageStrategy('ma_1', config)
```

### 4. Adaptive Strategy
Meta-strategy that combines multiple strategies with dynamic weights.

```python
from strategies import AdaptiveStrategy

config = {
    'strategies': [
        {'type': 'MeanReversion', 'weight': 0.5, 'config': {...}},
        {'type': 'TrendFollowing', 'weight': 0.5, 'config': {...}}
    ],
    'adjustment_period': 24  # hours
}
strategy = AdaptiveStrategy('adaptive_1', config)
```

## Creating Custom Strategies

### 1. Basic Strategy Template
```python
from typing import Dict, Any
import pandas as pd
from strategies import BaseStrategy

class CustomStrategy(BaseStrategy):
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name)
        # Initialize strategy-specific parameters
        self.param1 = config.get('param1', default_value)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on market data.
        
        Args:
            data: DataFrame with market data
                Required columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                
        Returns:
            pd.Series with values: 1 (buy), -1 (sell), 0 (hold)
        """
        # Implement your trading logic here
        signals = pd.Series(0, index=data.index)
        # ... your signal generation logic ...
        return signals
```

### 2. Strategy Requirements
- Must inherit from `BaseStrategy`
- Must implement `generate_signals` method
- Should handle missing/incomplete data
- Should include proper error handling
- Should be stateless or properly manage state

### 3. Best Practices
1. **Data Validation**
   ```python
   def generate_signals(self, data: pd.DataFrame) -> pd.Series:
       if len(data) < self.min_required_samples:
           return pd.Series(0, index=data.index)
       
       if not all(col in data.columns for col in ['close', 'volume']):
           raise ValueError("Missing required columns")
   ```

2. **Performance Optimization**
   ```python
   def generate_signals(self, data: pd.DataFrame) -> pd.Series:
       # Use vectorized operations
       ma = data['close'].rolling(window=self.ma_period).mean()
       signals = pd.Series(0, index=data.index)
       signals[data['close'] > ma] = 1
       signals[data['close'] < ma] = -1
       return signals
   ```

3. **Risk Management**
   ```python
   def apply_risk_management(self, signals: pd.Series, data: pd.DataFrame) -> pd.Series:
       # Apply position size limits
       signals = signals * self.max_position_size
       
       # Apply stop loss
       if self.current_position != 0:
           price_change = (data['close'] / self.entry_price - 1)
           if abs(price_change) > self.stop_loss_pct:
               signals[-1] = -self.current_position
               
       return signals
   ```

## Testing Strategies

### 1. Backtesting
```python
from backtesting import Backtester

# Initialize strategy
strategy = CustomStrategy('custom_1', config)

# Run backtest
backtester = Backtester(
    strategy=strategy,
    data=historical_data,
    initial_capital=10000,
    commission=0.001
)
results = backtester.run()
```

### 2. Unit Testing
```python
import unittest
import pandas as pd

class TestCustomStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = CustomStrategy('test', config)
        
    def test_signal_generation(self):
        data = pd.DataFrame({
            'close': [100, 101, 99, 102, 98],
            'volume': [1000] * 5
        })
        signals = self.strategy.generate_signals(data)
        self.assertEqual(len(signals), len(data))
```

## Performance Monitoring

### 1. Key Metrics
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Profit Factor
- Average Trade Return

### 2. Logging
```python
def generate_signals(self, data: pd.DataFrame) -> pd.Series:
    self.logger.info(f"Generating signals for {len(data)} candles")
    signals = super().generate_signals(data)
    self.logger.info(f"Generated {len(signals[signals != 0])} active signals")
    return signals
```

## Additional Resources
- [Strategy Development Guide](./development.md)
- [Backtesting Guide](./backtesting.md)
- [Risk Management Guide](./risk-management.md)
- [Performance Optimization](./optimization.md)
