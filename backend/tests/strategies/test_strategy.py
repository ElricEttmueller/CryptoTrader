import asyncio
import pandas as pd
from datetime import datetime, timedelta
from backend.strategies.ma_cross_strategy import MovingAverageCrossStrategy
from backend.database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def insert_test_data():
    """Insert some test historical price data."""
    db = DatabaseManager()
    try:
        await db.connect()
        
        # Generate test data
        end_time = datetime.utcnow()
        prices = []
        
        # Generate 30 days of hourly data
        for i in range(30 * 24):
            timestamp = end_time - timedelta(hours=i)
            base_price = 50000 + (i % 100) * 10  # Create some price movement
            
            prices.append({
                "symbol": "BTC/USD",
                "timeframe": "1h",
                "timestamp": timestamp,
                "open": base_price - 5,
                "high": base_price + 10,
                "low": base_price - 10,
                "close": base_price + 5,
                "volume": 1000 + i
            })
        
        # Insert the data
        logger.info("Inserting test historical price data...")
        count = await db.insert_historical_prices(prices)
        logger.info(f"Inserted {count} historical price records")
        
    finally:
        await db.close()

async def test_strategy():
    try:
        # First ensure we have test data
        await insert_test_data()
        
        # Create strategy instance
        strategy = MovingAverageCrossStrategy(
            user_id="test_user",
            short_window=10,
            long_window=20
        )

        # Set up test period
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)  # Test with 30 days of data

        # Run backtest
        logger.info("Starting backtest...")
        metrics = await strategy.run_backtest(
            symbol="BTC/USD",
            start_time=start_time,
            end_time=end_time,
            initial_capital=10000.0
        )

        # Print results
        logger.info("Backtest completed!")
        
        # Calculate and print performance metrics
        logger.info("Performance Metrics:")
        for key, value in metrics.items():
            if isinstance(value, float):
                logger.info(f"{key}: {value:.2f}")
            else:
                logger.info(f"{key}: {value}")

        db = DatabaseManager()
        await db.connect()
        user_id = "test_user"
        # Get all trades from database
        trades = await db.get_trades(user_id, "ma_cross")
        
        if trades:
            # Additional trade analysis
            profitable_trades = sum(1 for trade in trades if trade.get('profit', 0) > 0)
            total_trades = len(trades)
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_profit = sum(trade.get('profit', 0) for trade in trades)
            avg_profit_per_trade = total_profit / total_trades if total_trades > 0 else 0
            
            logger.info("\nDetailed Trade Analysis:")
            logger.info(f"Total Trades: {total_trades}")
            logger.info(f"Profitable Trades: {profitable_trades}")
            logger.info(f"Win Rate: {win_rate:.2f}%")
            logger.info(f"Average Profit per Trade: {avg_profit_per_trade:.2f}")
        await db.close()

    except Exception as e:
        logger.error(f"Error running strategy test: {str(e)}")
        raise
    finally:
        await strategy.close()

if __name__ == "__main__":
    asyncio.run(test_strategy())
