from typing import Dict, List, Type
import pandas as pd
from datetime import datetime, timedelta
import ccxt
from backend.strategies.base_strategy import BaseStrategy
from backend.database.db_manager import DatabaseManager
import numpy as np
import logging
import asyncio

class BacktestEngine:
    def __init__(self, 
                 initial_capital: float = 10000,
                 use_live_data: bool = False):
        """
        Initialize backtesting engine
        """
        self.exchange = ccxt.binance()
        self.initial_capital = initial_capital
        self.use_live_data = use_live_data
        self.db_manager = DatabaseManager() if use_live_data else None

    async def fetch_live_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical data from MongoDB
        """
        try:
            if not self.db_manager:
                await self.db_manager.connect()
            
            # Convert dates to datetime
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Fetch data from MongoDB
            historical_data = await self.db_manager.get_historical_prices(
                symbol=symbol,
                start_time=start_dt,
                end_time=end_dt,
                timeframe='1h'
            )
            
            if not historical_data:
                logging.warning(f"No historical data found for {symbol} from {start_date} to {end_date}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logging.error(f"Error fetching live historical data: {str(e)}")
            return pd.DataFrame()
        finally:
            if self.db_manager:
                await self.db_manager.close()

    def generate_synthetic_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Generate synthetic OHLCV data for testing
        """
        try:
            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)
            dates = pd.date_range(start=start_ts, end=end_ts, freq='1h')
            
            np.random.seed(42)  # For reproducibility
            
            # Generate synthetic price data with realistic patterns
            base_price = 40000  # Starting price
            volatility = 0.0015  # Daily volatility
            drift = 0.0001      # Small upward drift
            
            # Generate returns with momentum and mean reversion
            returns = np.zeros(len(dates))
            momentum = 0
            for i in range(len(dates)):
                # Combine random walk with momentum
                noise = np.random.normal(0, volatility)
                momentum = 0.95 * momentum + 0.05 * noise
                returns[i] = drift + momentum + 0.5 * noise
            
            # Generate price series
            price = base_price * np.exp(np.cumsum(returns))
            
            # Create OHLCV data with realistic relationships
            data = pd.DataFrame(index=dates)
            data['close'] = price
            
            # Generate open prices based on previous close
            data['open'] = np.roll(data['close'], 1)
            data.loc[data.index[0], 'open'] = data['close'].iloc[0] * (1 + np.random.normal(0, volatility))
            
            # Generate high and low with realistic ranges
            daily_range = price * volatility * 2
            data['high'] = data[['open', 'close']].max(axis=1) + abs(np.random.normal(0, 1, size=len(dates))) * daily_range
            data['low'] = data[['open', 'close']].min(axis=1) - abs(np.random.normal(0, 1, size=len(dates))) * daily_range
            
            # Generate volume with price-volume relationship
            base_volume = np.exp(10)  # Base volume level
            volume_volatility = 0.5    # Volume volatility
            
            # Higher volume on bigger price moves
            price_changes = np.abs(returns)
            volume_multiplier = 1 + 2 * price_changes  # More volume on larger price changes
            
            data['volume'] = base_volume * volume_multiplier * np.exp(np.random.normal(0, volume_volatility, size=len(dates)))
            
            # Ensure data consistency
            data['high'] = data[['high', 'open', 'close']].max(axis=1)
            data['low'] = data[['low', 'open', 'close']].min(axis=1)
            
            return data
            
        except Exception as e:
            logging.error(f"Error generating synthetic data: {str(e)}")
            return pd.DataFrame()

    async def fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from either MongoDB or generate synthetic data
        """
        if self.use_live_data:
            return await self.fetch_live_data(symbol, start_date, end_date)
        else:
            return self.generate_synthetic_data(start_date, end_date)

    async def run_backtest(self, strategy, symbol: str, start_date: str, end_date: str) -> Dict:
        """
        Run backtest for the given strategy
        """
        try:
            logging.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
            data = await self.fetch_data(symbol, start_date, end_date)
            if data.empty:
                logging.warning("No data available for the specified period")
                return None
            
            # Initialize variables
            position = 0
            trades = []
            portfolio_value = self.initial_capital
            
            # Train ML model if needed
            if hasattr(strategy, 'ml_strategy'):
                logging.info("Training ML model...")
                train_size = int(len(data) * 0.8)
                train_data = data.iloc[:train_size]
                strategy.ml_strategy.train_model(train_data)
                logging.info(f"Model accuracy - Train: {strategy.ml_strategy.model_accuracy:.4f}, Test: {strategy.ml_strategy.test_accuracy:.4f}")
            
            # Generate signals
            signals = strategy.generate_signals(data)
            
            # Simulate trading
            for i in range(1, len(data)):
                current_price = data['close'].iloc[i]
                signal = signals.iloc[i]
                
                # Execute trades based on signals with more flexible thresholds
                if signal > 0.3 and position <= 0:  # Buy signal
                    position = 1
                    trades.append({
                        'timestamp': data.index[i],
                        'side': 'buy',
                        'price': current_price,
                        'size': portfolio_value / current_price,
                        'value': portfolio_value
                    })
                    logging.info(f"BUY signal executed at {data.index[i]} - Price: {current_price}, Signal: {signal}")
                    
                elif signal < -0.3 and position >= 0:  # Sell signal
                    if position > 0:  # Calculate PnL only if we had a position
                        last_trade = next(t for t in reversed(trades) if t['side'] == 'buy')
                        pnl = (current_price - last_trade['price']) * last_trade['size']
                        portfolio_value += pnl
                        
                        trades.append({
                            'timestamp': data.index[i],
                            'side': 'sell',
                            'price': current_price,
                            'size': last_trade['size'],
                            'value': portfolio_value,
                            'pnl': pnl
                        })
                        logging.info(f"SELL signal executed at {data.index[i]} - Price: {current_price}, Signal: {signal}, PnL: {pnl}")
                    position = -1
            
            # Close any open position at the end
            if position != 0:
                current_price = data['close'].iloc[-1]
                if position > 0:
                    last_trade = next(t for t in reversed(trades) if t['side'] == 'buy')
                    pnl = (current_price - last_trade['price']) * last_trade['size']
                    portfolio_value += pnl
                    
                    trades.append({
                        'timestamp': data.index[-1],
                        'side': 'sell',
                        'price': current_price,
                        'size': last_trade['size'],
                        'value': portfolio_value,
                        'pnl': pnl
                    })
            
            # Calculate cumulative PnL
            if trades:
                trades_df = pd.DataFrame(trades)
                trades_df['cumulative_pnl'] = trades_df['pnl'].fillna(0).cumsum()
            
            return {
                'trades': trades,
                'final_portfolio_value': portfolio_value,
                'total_return': (portfolio_value - self.initial_capital) / self.initial_capital * 100,
                'prices': data['close']
            }
            
        except Exception as e:
            logging.error(f"Error in backtest: {str(e)}")
            return None

    async def plot_results(self, results: Dict) -> None:
        """
        Plot backtest results using plotly
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Handle empty trades case
            if not results['trades']:
                print("No trades were generated during the backtest.")
                # Create a simple price chart
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        y=results['prices'],
                        name="Price"
                    )
                )
                fig.update_layout(title="Price Chart (No Trades Generated)")
                fig.show()
                return
            
            # Create DataFrame from trades
            trades_df = pd.DataFrame(results['trades'])
            trades_df.set_index('timestamp', inplace=True)
            
            # Create figure with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add portfolio value line
            fig.add_trace(
                go.Scatter(
                    x=trades_df.index,
                    y=trades_df['value'],
                    name="Portfolio Value"
                ),
                secondary_y=False,
            )
            
            # Add trade markers
            buys = trades_df[trades_df['side'] == 'buy']
            sells = trades_df[trades_df['side'] == 'sell']
            
            fig.add_trace(
                go.Scatter(
                    x=buys.index,
                    y=buys['price'],
                    mode='markers',
                    name='Buy',
                    marker=dict(
                        symbol='triangle-up',
                        size=10,
                        color='green',
                    )
                ),
                secondary_y=True,
            )
            
            fig.add_trace(
                go.Scatter(
                    x=sells.index,
                    y=sells['price'],
                    mode='markers',
                    name='Sell',
                    marker=dict(
                        symbol='triangle-down',
                        size=10,
                        color='red',
                    )
                ),
                secondary_y=True,
            )
            
            # Update layout
            fig.update_layout(
                title=f"Backtest Results",
                xaxis_title="Date",
                yaxis_title="Portfolio Value",
                yaxis2_title="Price"
            )
            
            return fig
            
        except ImportError:
            logging.warning("Please install plotly to view results: pip install plotly")
