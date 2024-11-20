import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from backend.database.db_manager import DatabaseManager
from backend.strategies.adaptive_strategy import AdaptiveStrategy
from backend.strategies.ml_strategy import MLTradingStrategy
from backend.strategies.ma_strategy import MovingAverageStrategy
from backend.strategies.rl_strategy import RLTradingStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simplified format
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def generate_test_data():
    """Generate and insert test historical price data"""
    db = DatabaseManager()
    await db.connect()
    
    # Generate 1 year of hourly data
    periods = 365 * 24
    now = datetime.utcnow()
    dates = [now - timedelta(hours=x) for x in range(periods)]
    dates.reverse()
    
    import numpy as np
    
    # Generate price data with trends, volatility, and patterns
    base_price = 100
    trend = np.linspace(0, 20, periods)  # Overall upward trend
    volatility = np.random.normal(0, 1, periods)  # Random volatility
    cycle = 10 * np.sin(np.linspace(0, 8*np.pi, periods))  # Price cycles
    
    # Combine components
    prices = base_price + trend + volatility + cycle
    
    # Generate realistic OHLCV data
    data = []
    for i in range(periods):
        date = dates[i]
        close = prices[i]
        high = close * (1 + abs(np.random.normal(0, 0.02)))
        low = close * (1 - abs(np.random.normal(0, 0.02)))
        open_price = low + (high - low) * np.random.random()
        volume = np.random.normal(1000, 200)
        
        data.append({
            'timestamp': date,
            'symbol': 'BTC/USD',
            'open': float(open_price),
            'high': float(high),
            'low': float(low),
            'close': float(close),
            'volume': float(volume)
        })
    
    # Insert data into database
    await db.insert_historical_prices(data)
    logger.info("Generated and inserted historical data")
    
    await db.close()
    return data

async def test_adaptive_strategy():
    try:
        # Generate test data
        logger.info("Generating test data...")
        await generate_test_data()
        
        # Initialize strategies
        ml_strategy = MLTradingStrategy()
        ma_strategy = MovingAverageStrategy()
        rl_strategy = RLTradingStrategy()
        
        # Initialize adaptive strategy
        strategy = AdaptiveStrategy(ml_strategy, ma_strategy, rl_strategy)
        
        # Set up test parameters
        start_time = datetime.utcnow() - timedelta(days=365)
        end_time = datetime.utcnow()
        symbol = 'BTC/USD'
        initial_capital = 10000.0
        
        # Load data for backtesting
        db = DatabaseManager()
        await db.connect()
        
        logger.info("Running backtest...")
        
        # Load historical data
        data = await db.get_historical_prices(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            timeframe='1h'  # Using 1-hour timeframe
        )
        
        if not data:
            logger.error("No historical data found")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Train ML model first
        logger.info("Training ML model...")
        train_size = int(len(df) * 0.8)
        train_data = df.iloc[:train_size]
        ml_strategy.train_model(train_data)
        
        # Initialize portfolio tracking
        portfolio_value = initial_capital
        position = 0
        trades = []
        daily_returns = []
        regime_changes = []
        current_regime = None
        
        # Progress tracking
        total_steps = len(df)
        progress_interval = total_steps // 10  # Show progress every 10%
        
        # Run backtest
        for i in range(len(df)):
            if i < 50:  # Skip initial period to allow for indicator calculation
                continue
                
            # Show progress only at 10% intervals
            if i % progress_interval == 0:
                progress = (i / total_steps) * 100
                logger.info(f"Progress: {progress:.1f}%")
            
            # Get historical data up to current timestamp
            current_data = df.iloc[:i+1]
            
            # Get current regime info
            regime_info = strategy.get_current_regime_info(current_data)
            
            # Track regime changes
            if regime_info['regime'] != current_regime:
                regime_changes.append({
                    'timestamp': current_data.index[-1],
                    'old_regime': current_regime,
                    'new_regime': regime_info['regime'],
                    'portfolio_value': portfolio_value
                })
                current_regime = regime_info['regime']
            
            # Generate trading signal
            signal = strategy.generate_signals(current_data).iloc[-1]
            
            # Get current price
            current_price = current_data['close'].iloc[-1]
            
            # Execute trade
            if signal != 0:  # If we have a trade signal
                # Position size is now determined by the strategy
                new_position = signal
                
                if new_position > 0 and position <= 0:  # Buy signal
                    position = new_position
                    trades.append({
                        'timestamp': current_data.index[-1],
                        'type': 'buy',
                        'price': current_price,
                        'position': position,
                        'portfolio_value': portfolio_value,
                        'regime': regime_info['regime'],
                        'volatility': regime_info['volatility'],
                        'trend_strength': regime_info['trend_strength'],
                        'strategy_weights': regime_info['strategy_weights']
                    })
                elif new_position < 0 and position >= 0:  # Sell signal
                    position = new_position
                    trades.append({
                        'timestamp': current_data.index[-1],
                        'type': 'sell',
                        'price': current_price,
                        'position': position,
                        'portfolio_value': portfolio_value,
                        'regime': regime_info['regime'],
                        'volatility': regime_info['volatility'],
                        'trend_strength': regime_info['trend_strength'],
                        'strategy_weights': regime_info['strategy_weights']
                    })
            
            # Update portfolio value
            portfolio_value = initial_capital + position * current_price
            
            # Track daily returns
            if i > 0 and current_data.index[-1].date() != current_data.index[-2].date():
                daily_returns.append({
                    'date': current_data.index[-1].date(),
                    'return': (portfolio_value / initial_capital - 1) * 100
                })
        
        logger.info("Calculating performance metrics...")
        
        # Calculate performance metrics
        trades_df = pd.DataFrame(trades)
        daily_returns_df = pd.DataFrame(daily_returns)
        regime_changes_df = pd.DataFrame(regime_changes)
        
        # Basic metrics
        total_return = (portfolio_value / initial_capital - 1) * 100
        daily_returns_series = pd.Series([r['return'] for r in daily_returns])
        sharpe_ratio = daily_returns_series.mean() / daily_returns_series.std() * np.sqrt(252) if len(daily_returns_series) > 1 else 0
        max_drawdown = (pd.Series([t['portfolio_value'] for t in trades]).min() / initial_capital - 1) * 100
        
        # Advanced metrics
        win_rate = len(trades_df[trades_df['portfolio_value'] > trades_df['portfolio_value'].shift(1)]) / len(trades_df) if len(trades_df) > 0 else 0
        avg_trade_duration = np.mean([t['duration'][-1] for t in strategy.strategy_performance.values()]) if any(t['duration'] for t in strategy.strategy_performance.values()) else 0
        calmar_ratio = abs(total_return / max_drawdown) if max_drawdown != 0 else 0
        
        # Print results
        logger.info("\n=== Backtest Results ===")
        logger.info(f"Total Return: {total_return:.2f}%")
        logger.info(f"Number of Trades: {len(trades)}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        logger.info(f"Calmar Ratio: {calmar_ratio:.2f}")
        logger.info(f"Max Drawdown: {abs(max_drawdown):.2f}%")
        logger.info(f"Average Trade Duration: {avg_trade_duration:.1f} hours")
        
        # Analyze regime distribution
        regime_stats = trades_df.groupby('regime').agg({
            'type': 'count',
            'portfolio_value': lambda x: (x.iloc[-1] / x.iloc[0] - 1) * 100 if len(x) > 1 else 0,
            'volatility': 'mean',
            'trend_strength': 'mean'
        }).rename(columns={
            'type': 'trade_count',
            'portfolio_value': 'return'
        })
        
        logger.info("\n=== Regime Analysis ===")
        logger.info(regime_stats.to_string())
        
        # Strategy weight analysis
        logger.info("\n=== Final Strategy Weights ===")
        for regime in strategy.regime_strategy_weights:
            weights = strategy.regime_strategy_weights[regime]
            logger.info(f"{regime}: {weights}")
        
        await db.close()
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_adaptive_strategy())
