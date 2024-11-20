from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
from backend.strategies.base_strategy import BaseStrategy
from backend.database.db_manager import DatabaseManager

class DBStrategy(BaseStrategy):
    def __init__(self, name: str, user_id: str):
        super().__init__(name)
        self.user_id = user_id
        self.db = DatabaseManager()
        self.symbol = None
        # Initialize in constructor, will be connected when needed
        self._is_initialized = False

    async def ensure_initialized(self):
        """Ensure database is connected and strategy is initialized."""
        if not self._is_initialized:
            await self._initialize()
            self._is_initialized = True

    async def _initialize(self):
        """Initialize database connection and load strategy configuration."""
        await self.db.connect()
        config = await self.db.get_strategy_config(self.user_id, self.name)
        if config:
            # Load strategy parameters from database
            params = config.get('parameters', {})
            self.max_position_size = params.get('max_position_size', self.max_position_size)
            self.stop_loss_pct = params.get('stop_loss_pct', self.stop_loss_pct)
            self.take_profit_pct = params.get('take_profit_pct', self.take_profit_pct)

    async def save_config(self):
        """Save strategy configuration to database."""
        config = {
            'user_id': self.user_id,
            'strategy_name': self.name,
            'parameters': {
                'max_position_size': self.max_position_size,
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.take_profit_pct
            }
        }
        await self.db.save_strategy_config(config)

    async def load_historical_data(self, symbol: str, start_time: datetime, end_time: datetime, timeframe: str = "1h") -> pd.DataFrame:
        """Load historical price data from database."""
        await self.ensure_initialized()
        self.symbol = symbol
        data = await self.db.get_historical_prices(symbol, start_time, end_time, timeframe)
        return pd.DataFrame(data)

    async def save_signal(self, signal_type: int, price: float, params: Dict = None):
        """Save trading signal to database."""
        await self.ensure_initialized()
        if not self.symbol:
            raise ValueError("Symbol not set. Call load_historical_data first.")

        signal = {
            'symbol': self.symbol,
            'strategy': self.name,
            'signal_type': 'buy' if signal_type == 1 else 'sell' if signal_type == -1 else 'hold',
            'strength': 1.0,  # Can be customized based on strategy confidence
            'parameters': {
                'price': price,
                'stop_loss': price * (1 - self.stop_loss_pct) if signal_type == 1 else price * (1 + self.stop_loss_pct),
                'take_profit': price * (1 + self.take_profit_pct) if signal_type == 1 else price * (1 - self.take_profit_pct),
                **(params or {})
            }
        }
        await self.db.save_trading_signal(signal)

    async def save_trade(self, price: float, quantity: float):
        """Save executed trade to database."""
        await self.ensure_initialized()
        if not self.symbol:
            raise ValueError("Symbol not set. Call load_historical_data first.")

        trade = {
            'user_id': self.user_id,
            'symbol': self.symbol,
            'side': 'buy' if quantity > 0 else 'sell',
            'amount': abs(quantity),
            'price': price,
            'value': price * abs(quantity),
            'status': 'completed'
        }
        await self.db.insert_trade(trade)

    async def update_position(self):
        """Update position in database."""
        await self.ensure_initialized()
        if not self.symbol:
            raise ValueError("Symbol not set. Call load_historical_data first.")

        position = {
            'user_id': self.user_id,
            'symbol': self.symbol,
            'amount': self.position,
            'entry_price': sum(t['price'] * t['quantity'] for t in self.trades) / sum(t['quantity'] for t in self.trades) if self.trades else 0,
            'current_price': self.trades[-1]['price'] if self.trades else 0,
            'pnl': self.portfolio_value - self.trades[0]['portfolio_value'] if self.trades else 0
        }
        await self.db.upsert_position(position)

    async def save_portfolio_snapshot(self):
        """Save portfolio snapshot to database."""
        await self.ensure_initialized()
        snapshot = {
            'user_id': self.user_id,
            'total_value': self.portfolio_value,
            'positions': [{
                'symbol': self.symbol,
                'amount': self.position,
                'current_price': self.trades[-1]['price'] if self.trades else 0
            }] if self.symbol else [],
            'free_balance': self.cash
        }
        await self.db.save_portfolio_snapshot(snapshot)

    async def execute_trade(self, price: float, quantity: float, timestamp: pd.Timestamp):
        """Execute trade and update all relevant database records."""
        await self.ensure_initialized()
        # Update local state
        super().update_portfolio(price, quantity, timestamp)
        
        # Update database records
        await self.save_trade(price, quantity)
        await self.update_position()
        await self.save_portfolio_snapshot()

    async def close(self):
        """Close database connection."""
        await self.db.close()
