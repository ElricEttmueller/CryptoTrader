import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel
import logging
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
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

    async def create_collections(self):
        """Create all necessary collections with their indexes."""
        try:
            # Historical price data collection
            await self._setup_historical_prices()
            
            # Trades collection
            await self._setup_trades()
            
            # Positions collection
            await self._setup_positions()
            
            # Portfolio snapshots collection
            await self._setup_portfolio_snapshots()
            
            # Strategy configurations collection
            await self._setup_strategy_configs()
            
            # Trading signals collection
            await self._setup_trading_signals()
            
            logger.info("All collections and indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating collections: {str(e)}")
            raise

    async def _setup_historical_prices(self):
        """Set up historical prices collection."""
        collection = self.db.historical_prices
        indexes = [
            IndexModel([("symbol", ASCENDING), ("timestamp", DESCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("symbol", ASCENDING), ("timeframe", ASCENDING), ("timestamp", DESCENDING)], unique=True)
        ]
        await collection.create_indexes(indexes)
        logger.info("Historical prices collection setup complete")

    async def _setup_trades(self):
        """Set up trades collection."""
        collection = self.db.trades
        indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("symbol", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("strategy", ASCENDING)])
        ]
        await collection.create_indexes(indexes)
        logger.info("Trades collection setup complete")

    async def _setup_positions(self):
        """Set up positions collection."""
        collection = self.db.positions
        indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("symbol", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("symbol", ASCENDING)], unique=True)
        ]
        await collection.create_indexes(indexes)
        logger.info("Positions collection setup complete")

    async def _setup_portfolio_snapshots(self):
        """Set up portfolio snapshots collection."""
        collection = self.db.portfolio_snapshots
        indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        ]
        await collection.create_indexes(indexes)
        logger.info("Portfolio snapshots collection setup complete")

    async def _setup_strategy_configs(self):
        """Set up strategy configurations collection."""
        collection = self.db.strategy_configs
        indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("strategy_name", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("strategy_name", ASCENDING)], unique=True)
        ]
        await collection.create_indexes(indexes)
        logger.info("Strategy configurations collection setup complete")

    async def _setup_trading_signals(self):
        """Set up trading signals collection."""
        collection = self.db.trading_signals
        indexes = [
            IndexModel([("symbol", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),
            IndexModel([("strategy", ASCENDING)]),
            IndexModel([("symbol", ASCENDING), ("timestamp", DESCENDING), ("strategy", ASCENDING)])
        ]
        await collection.create_indexes(indexes)
        logger.info("Trading signals collection setup complete")

    async def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

async def main():
    """Initialize the database."""
    initializer = DatabaseInitializer()
    try:
        await initializer.connect()
        await initializer.create_collections()
    finally:
        await initializer.close()

if __name__ == "__main__":
    asyncio.run(main())
