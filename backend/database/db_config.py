from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self, mongodb_url: str = None, db_name: str = None):
        self.client: Optional[AsyncIOMotorClient] = None
        self.mongodb_url = mongodb_url or os.getenv('MONGODB_URL')
        self.db_name = db_name or os.getenv('MONGODB_DB_NAME', 'crypto_trader')
        self.db = None
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Connect to MongoDB Atlas."""
        try:
            # Set server timeout options
            self.client = AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=45000,
                maxPoolSize=100
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            
            self.db = self.client[self.db_name]
            
            # Create indexes
            await self._create_indexes()
            
            self.logger.info(f"Successfully connected to MongoDB Atlas database: {self.db_name}")
        except Exception as e:
            self.logger.error(f"Error connecting to MongoDB Atlas: {str(e)}")
            raise

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")

    async def _create_indexes(self):
        """Create necessary indexes for collections."""
        try:
            # Trades collection
            await self.db.trades.create_index([("timestamp", DESCENDING)])
            await self.db.trades.create_index([("symbol", ASCENDING), ("timestamp", DESCENDING)])
            await self.db.trades.create_index([("user_id", ASCENDING)])

            # Historical data collection
            await self.db.historical_data.create_index([
                ("symbol", ASCENDING),
                ("timestamp", DESCENDING),
                ("timeframe", ASCENDING)
            ])

            # Portfolio snapshots collection
            await self.db.portfolio_snapshots.create_index([
                ("user_id", ASCENDING),
                ("timestamp", DESCENDING)
            ])

            # User positions collection
            await self.db.positions.create_index([
                ("user_id", ASCENDING),
                ("symbol", ASCENDING)
            ], unique=True)

            # Strategy configurations collection
            await self.db.strategy_configs.create_index([
                ("user_id", ASCENDING),
                ("strategy_name", ASCENDING)
            ], unique=True)

            # Users collection
            await self.db.users.create_index([("email", ASCENDING)], unique=True)

            self.logger.info("Successfully created database indexes")
        except Exception as e:
            self.logger.error(f"Error creating indexes: {str(e)}")
            raise

    async def save_trade(self, trade_data: dict) -> str:
        """Save trade to database."""
        try:
            trade_data["timestamp"] = trade_data.get("timestamp", datetime.utcnow())
            result = await self.db.trades.insert_one(trade_data)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Error saving trade: {str(e)}")
            raise

    async def save_historical_data(self, symbol: str, timeframe: str, data: list) -> bool:
        """Save historical OHLCV data."""
        try:
            # Prepare bulk operation
            operations = [
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": candle[0],
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                }
                for candle in data
            ]
            
            if operations:
                await self.db.historical_data.insert_many(operations)
            return True
        except Exception as e:
            self.logger.error(f"Error saving historical data: {str(e)}")
            raise

    async def save_portfolio_snapshot(self, user_id: str, snapshot_data: dict) -> str:
        """Save portfolio snapshot."""
        try:
            snapshot_data.update({
                "user_id": user_id,
                "timestamp": datetime.utcnow()
            })
            result = await self.db.portfolio_snapshots.insert_one(snapshot_data)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Error saving portfolio snapshot: {str(e)}")
            raise

    async def update_position(self, user_id: str, position_data: dict) -> bool:
        """Update user position."""
        try:
            position_data["last_updated"] = datetime.utcnow()
            await self.db.positions.update_one(
                {
                    "user_id": user_id,
                    "symbol": position_data["symbol"]
                },
                {"$set": position_data},
                upsert=True
            )
            return True
        except Exception as e:
            self.logger.error(f"Error updating position: {str(e)}")
            raise

    async def get_positions(self, user_id: str) -> list:
        """Get all positions for a user."""
        try:
            cursor = self.db.positions.find({"user_id": user_id})
            return await cursor.to_list(length=None)
        except Exception as e:
            self.logger.error(f"Error getting positions: {str(e)}")
            raise

    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime = None
    ) -> list:
        """Get historical OHLCV data."""
        try:
            query = {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": {"$gte": start_time}
            }
            
            if end_time:
                query["timestamp"]["$lte"] = end_time
                
            cursor = self.db.historical_data.find(
                query,
                {"_id": 0}
            ).sort("timestamp", ASCENDING)
            
            return await cursor.to_list(length=None)
        except Exception as e:
            self.logger.error(f"Error getting historical data: {str(e)}")
            raise

    async def save_strategy_config(
        self,
        user_id: str,
        strategy_name: str,
        config: dict
    ) -> str:
        """Save strategy configuration."""
        try:
            config_data = {
                "user_id": user_id,
                "strategy_name": strategy_name,
                "config": config,
                "last_updated": datetime.utcnow()
            }
            
            result = await self.db.strategy_configs.update_one(
                {
                    "user_id": user_id,
                    "strategy_name": strategy_name
                },
                {"$set": config_data},
                upsert=True
            )
            
            return str(result.upserted_id) if result.upserted_id else "updated"
        except Exception as e:
            self.logger.error(f"Error saving strategy config: {str(e)}")
            raise

    async def get_strategy_config(
        self,
        user_id: str,
        strategy_name: str
    ) -> Optional[dict]:
        """Get strategy configuration."""
        try:
            config = await self.db.strategy_configs.find_one(
                {
                    "user_id": user_id,
                    "strategy_name": strategy_name
                },
                {"_id": 0}
            )
            return config
        except Exception as e:
            self.logger.error(f"Error getting strategy config: {str(e)}")
            raise

    # User Management Methods
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
        try:
            return await self.db.users.find_one({"email": email})
        except Exception as e:
            self.logger.error(f"Error getting user by email: {str(e)}")
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        try:
            from bson import ObjectId
            return await self.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            self.logger.error(f"Error getting user by ID: {str(e)}")
            raise

    async def create_user(self, user_data: dict):
        """Create a new user."""
        try:
            result = await self.db.users.insert_one(user_data)
            return result.inserted_id
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            raise

    async def update_user_login(self, user_id):
        """Update user's last login time."""
        try:
            await self.db.users.update_one(
                {"_id": user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except Exception as e:
            self.logger.error(f"Error updating user login: {str(e)}")
            raise

    async def add_api_key(self, user_id: str, api_key: dict) -> Optional[dict]:
        """Add an API key to user."""
        try:
            from bson import ObjectId
            result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"api_keys": api_key}}
            )
            if result.modified_count > 0:
                return await self.get_user_by_id(user_id)
            return None
        except Exception as e:
            self.logger.error(f"Error adding API key: {str(e)}")
            raise
