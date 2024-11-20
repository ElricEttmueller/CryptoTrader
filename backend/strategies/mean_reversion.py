import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from .base_strategy import BaseStrategy
import ta

class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy that trades based on price deviations from a moving average.
    When price deviates significantly from the moving average, it assumes the price will
    return to the mean.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the mean reversion strategy with configuration parameters.
        
        Args:
            config: Dictionary containing strategy parameters
                - window_size: Period for calculating moving average
                - std_dev_threshold: Number of standard deviations for entry/exit
                - position_size: Size of position to take
        """
        super().__init__(config)
        self.window_size = config.get('window_size', 20)
        self.std_dev_threshold = config.get('std_dev_threshold', 2.0)
        self.max_position_size = config.get('position_size', 0.1)
        
        # Initialize state variables
        self.moving_average = None
        self.std_dev = None
        
    async def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze market data and generate trading signals.
        
        Args:
            data: DataFrame containing market data with 'close' prices
            
        Returns:
            Dictionary containing analysis results and trading signals
        """
        # Need enough data points for analysis
        if len(data) < self.window_size:
            return {
                'signal': 'NEUTRAL',
                'confidence': 0.0,
                'position_size': 0.0
            }
            
        # Calculate moving average and standard deviation
        close_prices = data['close']
        ma = close_prices.rolling(window=self.window_size).mean()
        std = close_prices.rolling(window=self.window_size).std()
        
        # Calculate z-score (number of standard deviations from mean)
        z_score = (close_prices - ma) / std
        
        # Generate trading signals based on z-score
        if z_score.iloc[-1] < -self.std_dev_threshold:
            # Price is significantly below mean - buy signal
            confidence = min(abs(z_score.iloc[-1]) / (2 * self.std_dev_threshold), 1.0)
            return {
                'signal': 'BUY',
                'confidence': confidence,
                'position_size': self.max_position_size * confidence,
                'analysis': {
                    'moving_average': ma.iloc[-1],
                    'std_dev': std.iloc[-1],
                    'z_score': z_score.iloc[-1]
                }
            }
        elif z_score.iloc[-1] > self.std_dev_threshold:
            # Price is significantly above mean - sell signal
            confidence = min(abs(z_score.iloc[-1]) / (2 * self.std_dev_threshold), 1.0)
            return {
                'signal': 'SELL',
                'confidence': confidence,
                'position_size': self.max_position_size * confidence,
                'analysis': {
                    'moving_average': ma.iloc[-1],
                    'std_dev': std.iloc[-1],
                    'z_score': z_score.iloc[-1]
                }
            }
        else:
            # Price is within normal range
            return {
                'signal': 'NEUTRAL',
                'confidence': 0.0,
                'position_size': 0.0,
                'analysis': {
                    'moving_average': ma.iloc[-1],
                    'std_dev': std.iloc[-1],
                    'z_score': z_score.iloc[-1]
                }
            }
            
    def reset(self):
        """Reset the strategy state."""
        self.moving_average = None
        self.std_dev = None

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on mean reversion strategy.
        
        Args:
            data: DataFrame containing market data with 'close' prices
            
        Returns:
            Series of trading signals: 1 (buy), -1 (sell), 0 (hold)
        """
        if len(data) < self.window_size:
            return pd.Series(0, index=data.index)
        
        # Calculate moving average and standard deviation
        close_prices = data['close']
        ma = close_prices.rolling(window=self.window_size).mean()
        std = close_prices.rolling(window=self.window_size).std()
        
        # Calculate z-score (number of standard deviations from mean)
        z_score = (close_prices - ma) / std
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Buy when price is below mean by threshold std devs
        signals[z_score < -self.std_dev_threshold] = 1
        
        # Sell when price is above mean by threshold std devs
        signals[z_score > self.std_dev_threshold] = -1
        
        # Scale signals by position size
        signals = signals * self.max_position_size
        
        return signals
