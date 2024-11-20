import asyncio
import ccxt.async_support
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .websocket_manager import WebSocketManager

class MarketDataService:
    def __init__(self, websocket_manager: WebSocketManager, exchange_id: str = 'binance'):
        """Initialize Market Data Service"""
        self.ws_manager = websocket_manager
        self.exchange = getattr(ccxt.async_support, exchange_id)()
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.update_tasks: Dict[str, asyncio.Task] = {}
        
    async def start(self):
        """Start the market data service"""
        self.running = True
        self.logger.info("Market data service started")
        
    async def stop(self):
        """Stop the market data service"""
        self.running = False
        for symbol in list(self.update_tasks.keys()):
            await self.stop_price_updates(symbol)
        await self.exchange.close()
        self.logger.info("Market data service stopped")
        
    async def start_price_updates(self, symbol: str, interval: float = 1.0):
        """Start price updates for a symbol"""
        if symbol in self.update_tasks:
            return
            
        async def update_loop():
            while self.running:
                try:
                    ticker = await self.exchange.fetch_ticker(symbol)
                    await self.ws_manager.broadcast_price(
                        symbol=symbol,
                        price=ticker['last'],
                        timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000)
                    )
                    await asyncio.sleep(interval)
                except Exception as e:
                    self.logger.error(f"Error fetching price for {symbol}: {str(e)}")
                    await asyncio.sleep(5)  # Wait before retrying
                    
        self.update_tasks[symbol] = asyncio.create_task(update_loop())
        self.logger.info(f"Started price updates for {symbol}")
        
    async def stop_price_updates(self, symbol: str):
        """Stop price updates for a symbol"""
        if symbol in self.update_tasks:
            self.update_tasks[symbol].cancel()
            del self.update_tasks[symbol]
            self.logger.info(f"Stopped price updates for {symbol}")
            
    async def start_orderbook_updates(self, symbol: str, interval: float = 1.0):
        """Start orderbook updates for a symbol"""
        if symbol in self.update_tasks:
            return
            
        async def update_loop():
            while self.running:
                try:
                    orderbook = await self.exchange.fetch_order_book(symbol)
                    await self.ws_manager.broadcast_orderbook(
                        symbol=symbol,
                        bids=orderbook['bids'][:10],  # Top 10 bids
                        asks=orderbook['asks'][:10]    # Top 10 asks
                    )
                    await asyncio.sleep(interval)
                except Exception as e:
                    self.logger.error(f"Error fetching orderbook for {symbol}: {str(e)}")
                    await asyncio.sleep(5)  # Wait before retrying
                    
        self.update_tasks[symbol] = asyncio.create_task(update_loop())
        self.logger.info(f"Started orderbook updates for {symbol}")
        
    async def get_available_symbols(self) -> List[str]:
        """Get list of available trading pairs"""
        try:
            markets = await self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            self.logger.error(f"Error fetching markets: {str(e)}")
            return []

# Example usage:
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        # Create WebSocket manager and market data service
        ws_manager = WebSocketManager()
        market_service = MarketDataService(ws_manager)
        
        # Start services
        server_task = asyncio.create_task(ws_manager.start_server())
        await market_service.start()
        
        # Start updates for some symbols
        symbols = ['BTC/USDT', 'ETH/USDT']
        for symbol in symbols:
            await market_service.start_price_updates(symbol)
            await market_service.start_orderbook_updates(symbol)
            
        try:
            await server_task
        except KeyboardInterrupt:
            await market_service.stop()
            
    asyncio.run(main())
