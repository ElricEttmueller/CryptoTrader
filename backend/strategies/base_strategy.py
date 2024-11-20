from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.position = 0
        self.cash = 0
        self.portfolio_value = 0
        self.trades: List[Dict] = []
        self.max_position_size = 0.1  # Maximum 10% of portfolio in one position
        self.stop_loss_pct = 0.02     # 2% stop loss
        self.take_profit_pct = 0.04   # 4% take profit

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the input data.
        Returns a pandas Series with values: 1 (buy), -1 (sell), 0 (hold)
        """
        pass

    def calculate_position_size(self, signal: int, price: float) -> Optional[float]:
        """
        Calculate the position size for a trade based on the signal and current price
        Returns the quantity to trade (positive for buy, negative for sell)
        """
        if signal == 0 or price <= 0:
            return None
        
        # Risk-based position sizing
        risk_amount = self.portfolio_value * self.stop_loss_pct
        max_position_value = self.portfolio_value * self.max_position_size
        
        # Calculate position size based on risk
        position_size = min(
            risk_amount / (price * self.stop_loss_pct),  # Risk-based size
            max_position_value / price                    # Max position size
        )
        
        # Ensure we have enough cash for the trade
        if signal == 1:  # Buy
            max_affordable = self.cash / price
            position_size = min(position_size, max_affordable)
        
        return position_size if signal == 1 else -position_size

    def update_portfolio(self, price: float, quantity: float, timestamp: pd.Timestamp):
        """
        Update portfolio after executing a trade
        """
        trade_value = price * abs(quantity)
        
        if quantity > 0:  # Buy
            self.cash -= trade_value
        else:  # Sell
            self.cash += trade_value
        
        self.position += quantity
        self.portfolio_value = self.cash + (self.position * price)
        
        self.trades.append({
            'timestamp': timestamp,
            'price': price,
            'quantity': quantity,
            'value': trade_value,
            'portfolio_value': self.portfolio_value,
            'cash': self.cash,
            'position': self.position
        })

    def get_performance_metrics(self) -> Dict:
        """
        Calculate strategy performance metrics
        """
        if not self.trades:
            return {}

        df = pd.DataFrame(self.trades)
        
        # Calculate daily returns
        df['daily_returns'] = df['portfolio_value'].pct_change()
        
        # Calculate metrics
        total_return = (self.portfolio_value / self.trades[0]['portfolio_value'] - 1) * 100
        
        # Annualized Sharpe Ratio (assuming risk-free rate of 0.02)
        risk_free_rate = 0.02
        excess_returns = df['daily_returns'] - risk_free_rate/252
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * (252 ** 0.5) if len(excess_returns) > 1 else 0
        
        # Maximum Drawdown
        rolling_max = df['portfolio_value'].expanding().max()
        drawdowns = (df['portfolio_value'] - rolling_max) / rolling_max
        max_drawdown = abs(drawdowns.min()) * 100 if not drawdowns.empty else 0
        
        # Win Rate
        profitable_trades = sum(t['value'] > 0 for t in self.trades)
        win_rate = (profitable_trades / len(self.trades)) * 100 if self.trades else 0
        
        metrics = {
            'total_return': total_return,
            'num_trades': len(self.trades),
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate
        }
        
        return metrics
