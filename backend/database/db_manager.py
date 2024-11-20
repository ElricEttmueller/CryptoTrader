from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.mongodb_url = os.getenv('MONGODB_URL')
        self.db_name = os.getenv('MONGODB_DB_NAME')
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB Atlas."""
        try:
            self.client = AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=100
            )
            self.db = self.client[self.db_name]
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {self.db_name}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise

    async def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

    # Historical Price Methods
    async def insert_historical_prices(self, prices: List[Dict]):
        """Insert historical price data."""
        try:
            result = await self.db.historical_prices.insert_many(prices)
            return len(result.inserted_ids)
        except Exception as e:
            logger.error(f"Error inserting historical prices: {str(e)}")
            raise

    async def get_historical_prices(self, symbol: str, start_time: datetime, end_time: datetime, timeframe: str):
        """Retrieve historical price data."""
        try:
            query = {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
            cursor = self.db.historical_prices.find(query).sort("timestamp", 1)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving historical prices: {str(e)}")
            raise

    # Trade Methods
    async def insert_trade(self, trade: Dict):
        """Insert a new trade."""
        try:
            trade['timestamp'] = datetime.utcnow()
            result = await self.db.trades.insert_one(trade)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error inserting trade: {str(e)}")
            raise

    async def get_trades(self, user_id: str, symbol: Optional[str] = None, limit: int = 100):
        """Retrieve trades for a user."""
        try:
            query = {"user_id": user_id}
            if symbol:
                query["symbol"] = symbol
            cursor = self.db.trades.find(query).sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving trades: {str(e)}")
            raise

    async def save_trade(self, trade: Dict):
        """Save trade information to the trades collection."""
        collection = self.db['trades']
        await collection.insert_one(trade)

    # Position Methods
    async def upsert_position(self, position: Dict):
        """Update or insert a position."""
        try:
            query = {
                "user_id": position["user_id"],
                "symbol": position["symbol"]
            }
            position['last_updated'] = datetime.utcnow()
            result = await self.db.positions.update_one(
                query,
                {"$set": position},
                upsert=True
            )
            return result.upserted_id or result.modified_count
        except Exception as e:
            logger.error(f"Error upserting position: {str(e)}")
            raise

    async def get_positions(self, user_id: str):
        """Get all positions for a user."""
        try:
            cursor = self.db.positions.find({"user_id": user_id})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving positions: {str(e)}")
            raise

    # Portfolio Methods
    async def save_portfolio_snapshot(self, snapshot: Dict):
        """Save a portfolio snapshot."""
        try:
            snapshot['timestamp'] = datetime.utcnow()
            result = await self.db.portfolio_snapshots.insert_one(snapshot)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error saving portfolio snapshot: {str(e)}")
            raise

    async def get_portfolio_history(self, user_id: str, start_time: datetime, end_time: datetime):
        """Get portfolio history for a time period."""
        try:
            query = {
                "user_id": user_id,
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
            cursor = self.db.portfolio_snapshots.find(query).sort("timestamp", 1)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving portfolio history: {str(e)}")
            raise

    # Strategy Methods
    async def save_strategy_config(self, config: Dict):
        """Save a strategy configuration."""
        try:
            config['last_updated'] = datetime.utcnow()
            query = {
                "user_id": config["user_id"],
                "strategy_name": config["strategy_name"]
            }
            result = await self.db.strategy_configs.update_one(
                query,
                {"$set": config},
                upsert=True
            )
            return result.upserted_id or result.modified_count
        except Exception as e:
            logger.error(f"Error saving strategy config: {str(e)}")
            raise

    async def get_strategy_config(self, user_id: str, strategy_name: str):
        """Get a strategy configuration."""
        try:
            return await self.db.strategy_configs.find_one({
                "user_id": user_id,
                "strategy_name": strategy_name
            })
        except Exception as e:
            logger.error(f"Error retrieving strategy config: {str(e)}")
            raise

    # Signal Methods
    async def save_trading_signal(self, signal: Dict):
        """Save a trading signal."""
        try:
            signal['timestamp'] = datetime.utcnow()
            result = await self.db.trading_signals.insert_one(signal)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error saving trading signal: {str(e)}")
            raise

    async def get_trading_signals(self, symbol: str, strategy: str, start_time: datetime, end_time: datetime):
        """Get trading signals for a symbol and strategy."""
        try:
            query = {
                "symbol": symbol,
                "strategy": strategy,
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
            cursor = self.db.trading_signals.find(query).sort("timestamp", -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error retrieving trading signals: {str(e)}")
            raise
