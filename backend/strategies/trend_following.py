import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from .base_strategy import BaseStrategy
import ta

class TrendFollowingStrategy(BaseStrategy):
    """
    Trend Following Strategy that trades in the direction of established trends.
    Uses moving averages and momentum indicators to identify and trade trends.
    """
    
    def __init__(self, name: str = "Trend Following"):
        """
        Initialize the trend following strategy.
        """
        super().__init__(name)
        self.fast_window = 10
        self.slow_window = 30
        self.momentum_window = 14
        self.max_position_size = 0.1
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on trend following strategy.
        
        Args:
            data: DataFrame containing market data with OHLCV data
            
        Returns:
            Series of trading signals: 1 (buy), -1 (sell), 0 (hold)
        """
        if len(data) < self.slow_window:
            return pd.Series(0, index=data.index)
            
        # Calculate indicators
        fast_ma = data['close'].rolling(window=self.fast_window).mean()
        slow_ma = data['close'].rolling(window=self.slow_window).mean()
        rsi = ta.momentum.rsi(data['close'], window=self.momentum_window)
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Buy conditions:
        # 1. Fast MA crosses above Slow MA (uptrend)
        # 2. RSI indicates momentum (> 50)
        buy_condition = (
            (fast_ma > slow_ma) & 
            (rsi > 50)
        )
        signals[buy_condition] = 1
        
        # Sell conditions:
        # 1. Fast MA crosses below Slow MA (downtrend)
        # 2. RSI indicates weakness (< 50)
        sell_condition = (
            (fast_ma < slow_ma) & 
            (rsi < 50)
        )
        signals[sell_condition] = -1
        
        # Scale signals by position size
        signals = signals * self.max_position_size
        
        return signals
        
    def reset(self):
        """Reset the strategy state."""
        pass  # No state to reset for this strategy

    async def analyze(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze market data and generate trading signals.
        
        Args:
            market_data: DataFrame containing market data with OHLCV data
            
        Returns:
            Dictionary containing analysis results and trading signals
        """
        # Generate signals
        signals = self.generate_signals(market_data)
        
        # Get the last signal
        signal = signals.iloc[-1]
        
        # Map signal to strategy output
        if signal > 0:
            return {
                'signal': 'BUY',
                'confidence': 1.0,
                'position_size': self.max_position_size
            }
        elif signal < 0:
            return {
                'signal': 'SELL',
                'confidence': 1.0,
                'position_size': self.max_position_size
            }
        else:
            return {
                'signal': 'NEUTRAL',
                'confidence': 0.0,
                'position_size': 0.0
            }
