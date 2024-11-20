import sys
import os
import asyncio
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import List, Dict

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fetch_historical_data(
    exchange: ccxt.Exchange,
    symbol: str,
    timeframe: str = '1h',
    start_date: datetime = None,
    end_date: datetime = None
) -> List[Dict]:
    """
    Fetch historical OHLCV data from exchange
    """
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Convert dates to timestamps
        since = int(start_date.timestamp() * 1000)
        until = int(end_date.timestamp() * 1000)

        # Fetch data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, until)
        
        # Convert to list of dictionaries
        historical_data = []
        for timestamp, open_price, high, low, close, volume in ohlcv:
            historical_data.append({
                'timestamp': datetime.fromtimestamp(timestamp / 1000),
                'symbol': symbol,
                'timeframe': timeframe,
                'open': float(open_price),
                'high': float(high),
                'low': float(low),
                'close': float(close),
                'volume': float(volume)
            })
        
        return historical_data

    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return []

async def main():
    try:
        # Initialize exchange (Binance)
        exchange = ccxt.binance()
        
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.connect()
        
        # Define parameters
        symbols = ['BTC/USDT', 'ETH/USDT']  # Add more symbols as needed
        timeframes = ['1h']  # Add more timeframes if needed
        start_date = datetime.now() - timedelta(days=365)  # Last year
        end_date = datetime.now()
        
        # Fetch and store data for each symbol and timeframe
        for symbol in symbols:
            for timeframe in timeframes:
                logger.info(f"Fetching {timeframe} data for {symbol}...")
                
                historical_data = await fetch_historical_data(
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if historical_data:
                    # Store in database
                    inserted_count = await db_manager.insert_historical_prices(historical_data)
                    logger.info(f"Inserted {inserted_count} records for {symbol} ({timeframe})")
                else:
                    logger.warning(f"No data fetched for {symbol} ({timeframe})")
        
        # Close database connection
        await db_manager.close()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
