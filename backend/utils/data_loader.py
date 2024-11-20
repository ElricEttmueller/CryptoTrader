import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class DataLoader:
    def __init__(self, exchange_name: str = 'binance'):
        """Initialize DataLoader with specified exchange"""
        self.exchange = getattr(ccxt, exchange_name)()
        
    def get_live_data(self, pair: str) -> Dict:
        """Get live market data for a trading pair"""
        try:
            ticker = self.exchange.fetch_ticker(pair)
            return {
                'symbol': ticker['symbol'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            raise Exception(f"Error fetching live data: {str(e)}")

    def get_historical_data(
        self,
        pair: str,
        timeframe: str = "1d",
        limit: int = 100,
        since: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for a trading pair
        
        Args:
            pair: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Time interval (e.g., '1m', '1h', '1d')
            limit: Number of candles to fetch
            since: Start time in ISO format
        """
        try:
            if since:
                since_ts = int(datetime.fromisoformat(since).timestamp() * 1000)
            else:
                since_ts = None

            ohlcv = self.exchange.fetch_ohlcv(
                symbol=pair,
                timeframe=timeframe,
                limit=limit,
                since=since_ts
            )

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            raise Exception(f"Error fetching historical data: {str(e)}")

    def get_orderbook(self, pair: str, limit: int = 10) -> Dict:
        """Get current orderbook for a trading pair"""
        try:
            orderbook = self.exchange.fetch_order_book(pair, limit)
            return {
                'bids': orderbook['bids'],
                'asks': orderbook['asks'],
                'timestamp': orderbook['timestamp']
            }
        except Exception as e:
            raise Exception(f"Error fetching orderbook: {str(e)}")

    def get_recent_trades(self, pair: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a trading pair"""
        try:
            trades = self.exchange.fetch_trades(pair, limit=limit)
            return [{
                'timestamp': trade['timestamp'],
                'price': trade['price'],
                'amount': trade['amount'],
                'side': trade['side']
            } for trade in trades]
        except Exception as e:
            raise Exception(f"Error fetching recent trades: {str(e)}")

    def get_markets(self) -> List[str]:
        """Get list of available trading pairs"""
        try:
            self.exchange.load_markets()
            return list(self.exchange.markets.keys())
        except Exception as e:
            raise Exception(f"Error fetching markets: {str(e)}")
