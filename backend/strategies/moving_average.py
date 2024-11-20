import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MovingAverageStrategy(BaseStrategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        super().__init__('Moving Average Crossover')
        self.short_window = short_window
        self.long_window = long_window
        self.stop_loss_pct = 0.02     # 2% stop loss
        self.take_profit_pct = 0.04   # 4% take profit
        self.last_buy_price = None

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Moving Average Crossover strategy
        Returns 1 for buy, -1 for sell, 0 for hold
        """
        # Calculate moving averages
        short_ma = data['close'].rolling(window=self.short_window, min_periods=1).mean()
        long_ma = data['close'].rolling(window=self.long_window, min_periods=1).mean()
        
        # Initialize signals
        signals = pd.Series(0, index=data.index)
        
        # Calculate crossover signals
        golden_cross = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        death_cross = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
        
        # Generate basic signals from crossovers
        signals[golden_cross] = 1
        signals[death_cross] = -1
        
        # Add momentum filter
        rsi = self.calculate_rsi(data['close'])
        
        # Only buy if RSI is below 70 (not overbought)
        signals[rsi > 70] = 0
        
        # Only sell if RSI is above 30 (not oversold)
        signals[rsi < 30] = 0
        
        # Apply stop loss and take profit
        for i in range(1, len(data)):
            if self.position > 0:  # We have a long position
                price_change = (data['close'].iloc[i] - self.last_buy_price) / self.last_buy_price
                
                # Check stop loss
                if price_change < -self.stop_loss_pct:
                    signals.iloc[i] = -1  # Sell
                
                # Check take profit
                elif price_change > self.take_profit_pct:
                    signals.iloc[i] = -1  # Take profit
            
            # Update last buy price when we enter a new position
            if signals.iloc[i] == 1:
                self.last_buy_price = data['close'].iloc[i]
        
        return signals

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
