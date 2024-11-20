import asyncio
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_operations():
    db = DatabaseManager()
    try:
        # Connect to database
        await db.connect()
        
        # Test user ID
        user_id = "test_user"
        
        # Test historical prices
        prices = [
            {
                "symbol": "BTC/USD",
                "timeframe": "1h",
                "timestamp": datetime.utcnow() - timedelta(hours=i),
                "open": 50000 + i,
                "high": 51000 + i,
                "low": 49000 + i,
                "close": 50500 + i,
                "volume": 100 + i
            }
            for i in range(5)
        ]
        
        logger.info("Testing historical price insertion...")
        inserted_count = await db.insert_historical_prices(prices)
        logger.info(f"Inserted {inserted_count} historical price records")
        
        # Test trade insertion
        trade = {
            "user_id": user_id,
            "symbol": "BTC/USD",
            "side": "buy",
            "amount": 0.1,
            "price": 50000,
            "status": "completed"
        }
        
        logger.info("Testing trade insertion...")
        trade_id = await db.insert_trade(trade)
        logger.info(f"Inserted trade with ID: {trade_id}")
        
        # Test position upsert
        position = {
            "user_id": user_id,
            "symbol": "BTC/USD",
            "amount": 0.1,
            "entry_price": 50000,
            "current_price": 51000,
            "pnl": 100
        }
        
        logger.info("Testing position upsert...")
        position_result = await db.upsert_position(position)
        logger.info(f"Upserted position with result: {position_result}")
        
        # Test portfolio snapshot
        snapshot = {
            "user_id": user_id,
            "total_value": 5100,
            "positions": [position],
            "free_balance": 1000
        }
        
        logger.info("Testing portfolio snapshot...")
        snapshot_id = await db.save_portfolio_snapshot(snapshot)
        logger.info(f"Saved portfolio snapshot with ID: {snapshot_id}")
        
        # Test strategy config
        strategy_config = {
            "user_id": user_id,
            "strategy_name": "simple_ma_cross",
            "parameters": {
                "short_window": 10,
                "long_window": 20,
                "symbols": ["BTC/USD"]
            }
        }
        
        logger.info("Testing strategy config save...")
        config_result = await db.save_strategy_config(strategy_config)
        logger.info(f"Saved strategy config with result: {config_result}")
        
        # Test trading signal
        signal = {
            "symbol": "BTC/USD",
            "strategy": "simple_ma_cross",
            "signal_type": "buy",
            "strength": 0.8,
            "parameters": {
                "price": 50000,
                "target": 52000,
                "stop_loss": 49000
            }
        }
        
        logger.info("Testing trading signal save...")
        signal_id = await db.save_trading_signal(signal)
        logger.info(f"Saved trading signal with ID: {signal_id}")
        
        # Test retrievals
        logger.info("Testing data retrieval...")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=1)
        
        historical_prices = await db.get_historical_prices("BTC/USD", start_time, end_time, "1h")
        logger.info(f"Retrieved {len(historical_prices)} historical price records")
        
        trades = await db.get_trades(user_id)
        logger.info(f"Retrieved {len(trades)} trades")
        
        positions = await db.get_positions(user_id)
        logger.info(f"Retrieved {len(positions)} positions")
        
        portfolio_history = await db.get_portfolio_history(user_id, start_time, end_time)
        logger.info(f"Retrieved {len(portfolio_history)} portfolio snapshots")
        
        strategy = await db.get_strategy_config(user_id, "simple_ma_cross")
        logger.info(f"Retrieved strategy config: {strategy['strategy_name'] if strategy else None}")
        
        signals = await db.get_trading_signals("BTC/USD", "simple_ma_cross", start_time, end_time)
        logger.info(f"Retrieved {len(signals)} trading signals")
        
    except Exception as e:
        logger.error(f"Error during database operations: {str(e)}")
        raise
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_database_operations())
