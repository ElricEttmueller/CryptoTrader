import pandas as pd
from typing import Dict
from backend.strategies.db_strategy import DBStrategy

class MovingAverageCrossStrategy(DBStrategy):
    def __init__(self, user_id: str, short_window: int = 9, long_window: int = 21):
        super().__init__("ma_cross", user_id)
        self.short_window = short_window
        self.long_window = long_window
        self.stop_loss_pct = 0.02  # 2% stop loss
        self.take_profit_pct = 0.04  # 4% take profit
        self.max_position_size = 0.2  # Maximum 20% of portfolio per trade
        self.min_volume = 1000  # Minimum volume threshold

    async def _initialize(self):
        """Initialize strategy with configuration from database."""
        await super()._initialize()
        config = await self.db.get_strategy_config(self.user_id, self.name)
        if config:
            params = config.get('parameters', {})
            self.short_window = params.get('short_window', self.short_window)
            self.long_window = params.get('long_window', self.long_window)
        else:
            # Save initial configuration without calling ensure_initialized
            config = {
                'user_id': self.user_id,
                'strategy_name': self.name,
                'parameters': {
                    'short_window': self.short_window,
                    'long_window': self.long_window,
                    'max_position_size': self.max_position_size,
                    'stop_loss_pct': self.stop_loss_pct,
                    'take_profit_pct': self.take_profit_pct
                }
            }
            await self.db.save_strategy_config(config)

    async def save_config(self):
        """Save strategy configuration to database."""
        await self.ensure_initialized()
        config = {
            'user_id': self.user_id,
            'strategy_name': self.name,
            'parameters': {
                'short_window': self.short_window,
                'long_window': self.long_window,
                'max_position_size': self.max_position_size,
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.take_profit_pct
            }
        }
        await self.db.save_strategy_config(config)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on moving average crossover with additional filters."""
        if len(data) < self.long_window:
            return pd.Series(0, index=data.index)

        # Calculate moving averages
        short_ma = data['close'].rolling(window=self.short_window).mean()
        long_ma = data['close'].rolling(window=self.long_window).mean()
        
        # Calculate additional technical indicators
        # Exponential moving averages for trend confirmation
        ema_50 = data['close'].ewm(span=50, adjust=False).mean()
        
        # Calculate volatility using ATR (Average True Range)
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        atr = ranges.max(axis=1).rolling(window=14).mean()
        
        # Volume moving average
        volume_ma = data['volume'].rolling(window=20).mean()

        # Generate base signals
        signals = pd.Series(0, index=data.index)
        
        # Long signal conditions
        long_conditions = (
            (short_ma > long_ma) &  # MA crossover
            (data['close'] > ema_50) &  # Price above EMA50 (uptrend)
            (data['volume'] > volume_ma) &  # Above average volume
            (data['volume'] > self.min_volume)  # Minimum volume threshold
        )
        
        # Short signal conditions
        short_conditions = (
            (short_ma < long_ma) &  # MA crossover
            (data['close'] < ema_50) &  # Price below EMA50 (downtrend)
            (data['volume'] > volume_ma) &  # Above average volume
            (data['volume'] > self.min_volume)  # Minimum volume threshold
        )

        signals[long_conditions] = 1
        signals[short_conditions] = -1

        # Remove signals during the warm-up period
        signals.iloc[:self.long_window] = 0
        
        # Filter out signals in high volatility periods
        volatility_threshold = atr.rolling(window=14).mean() * 2
        signals[atr > volatility_threshold] = 0

        return signals

    def calculate_position_size(self, signal: int, price: float) -> float:
        """Calculate position size based on risk management rules."""
        if signal == 0:
            return 0

        # Calculate maximum position size based on portfolio value
        max_trade_value = self.portfolio_value * self.max_position_size
        
        # Calculate position size based on stop loss
        risk_amount = self.portfolio_value * 0.01  # Risk 1% of portfolio per trade
        stop_loss_distance = price * self.stop_loss_pct
        position_size = risk_amount / stop_loss_distance
        
        # Limit position size to maximum trade value
        position_size = min(position_size, max_trade_value / price)
        
        return position_size if signal == 1 else -position_size

    async def execute_trade(self, price: float, quantity: float, timestamp: pd.Timestamp):
        """Execute trade with stop loss and take profit orders."""
        if quantity == 0:
            return

        # Calculate stop loss and take profit prices
        stop_loss = price * (1 - self.stop_loss_pct) if quantity > 0 else price * (1 + self.stop_loss_pct)
        take_profit = price * (1 + self.take_profit_pct) if quantity > 0 else price * (1 - self.take_profit_pct)

        # Calculate profit/loss if closing a position
        profit = 0
        if (self.position > 0 and quantity < 0) or (self.position < 0 and quantity > 0):
            # Calculate profit based on previous position
            prev_position_value = self.position * self.last_price if hasattr(self, 'last_price') else 0
            new_position_value = self.position * price
            profit = new_position_value - prev_position_value

        trade = {
            'user_id': self.user_id,
            'strategy_name': self.name,
            'symbol': self.symbol,
            'timestamp': timestamp,
            'price': price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'portfolio_value': self.portfolio_value,
            'profit': profit
        }

        # Update position and cash
        trade_value = price * abs(quantity)
        self.position += quantity
        self.cash -= trade_value
        self.portfolio_value = self.cash + (self.position * price)
        self.last_price = price

        # Save trade to database
        await self.db.save_trade(trade)

    async def run_backtest(self, symbol: str, start_time: pd.Timestamp, end_time: pd.Timestamp, 
                          initial_capital: float = 10000.0):
        """Run backtest and save results to database."""
        # Initialize portfolio
        self.cash = initial_capital
        self.portfolio_value = initial_capital
        self.position = 0
        self.trades = []

        # Load historical data
        data = await self.load_historical_data(symbol, start_time, end_time)
        
        # Generate signals
        signals = self.generate_signals(data)

        # Iterate through the data
        for timestamp, row in data.iterrows():
            price = row['close']
            signal = signals[timestamp]

            # Calculate position size
            quantity = self.calculate_position_size(signal, price)
            
            if quantity:
                # Save signal to database
                signal_params = {
                    'short_ma': data['close'].rolling(window=self.short_window).mean()[timestamp],
                    'long_ma': data['close'].rolling(window=self.long_window).mean()[timestamp]
                }
                await self.save_signal(signal, price, signal_params)
                
                # Execute trade
                await self.execute_trade(price, quantity, timestamp)

        # Calculate and save final metrics
        metrics = self.get_performance_metrics()
        
        # Save final portfolio snapshot
        await self.save_portfolio_snapshot()

        return metrics
