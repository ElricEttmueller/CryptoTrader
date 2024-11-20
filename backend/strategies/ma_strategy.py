import pandas as pd
import numpy as np
import ta
from typing import Dict
from .base_strategy import BaseStrategy

class MovingAverageStrategy(BaseStrategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        Initialize Moving Average trading strategy
        """
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on moving average crossovers
        """
        try:
            if len(data) < self.long_window:
                return pd.Series(0, index=data.index)
            
            # Calculate moving averages
            short_ma = ta.trend.sma_indicator(data['close'], window=self.short_window)
            long_ma = ta.trend.sma_indicator(data['close'], window=self.long_window)
            
            # Generate signals
            signals = pd.Series(0, index=data.index)
            
            # Buy when short MA crosses above long MA
            signals[short_ma > long_ma] = 1
            
            # Sell when short MA crosses below long MA
            signals[short_ma < long_ma] = -1
            
            return signals
            
        except Exception as e:
            print(f"Error generating MA signals: {str(e)}")
            return pd.Series(0, index=data.index)
    
    def calculate_ma_metrics(self, data: pd.DataFrame) -> Dict:
        """
        Calculate various moving average based metrics
        """
        try:
            if len(data) < self.long_window:
                return {}
            
            # Calculate moving averages
            short_ma = ta.trend.sma_indicator(data['close'], window=self.short_window)
            long_ma = ta.trend.sma_indicator(data['close'], window=self.long_window)
            
            # Calculate metrics
            ma_diff = (short_ma - long_ma) / long_ma * 100  # Percentage difference
            ma_slope = short_ma.diff() / short_ma * 100  # Rate of change
            
            return {
                'ma_diff': ma_diff.iloc[-1],
                'ma_slope': ma_slope.iloc[-1],
                'short_ma': short_ma.iloc[-1],
                'long_ma': long_ma.iloc[-1]
            }
            
        except Exception as e:
            print(f"Error calculating MA metrics: {str(e)}")
            return {}
