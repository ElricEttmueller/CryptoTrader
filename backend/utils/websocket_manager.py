import asyncio
import json
import logging
import websockets
from typing import Dict, List, Optional, Callable
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        """Initialize WebSocket Manager"""
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # client_id -> symbols
        self.symbol_subscribers: Dict[str, List[str]] = {}  # symbol -> client_ids
        self.last_prices: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)
        
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client connection"""
        client_id = str(id(websocket))
        self.connections[client_id] = websocket
        self.subscriptions[client_id] = []
        self.logger.info(f"Client {client_id} connected")
        return client_id

    async def unregister(self, client_id: str):
        """Unregister a client connection"""
        if client_id in self.connections:
            # Remove from subscriptions
            symbols = self.subscriptions.get(client_id, [])
            for symbol in symbols:
                if symbol in self.symbol_subscribers:
                    self.symbol_subscribers[symbol].remove(client_id)
                    if not self.symbol_subscribers[symbol]:
                        del self.symbol_subscribers[symbol]
            
            # Clean up connection data
            del self.connections[client_id]
            del self.subscriptions[client_id]
            self.logger.info(f"Client {client_id} disconnected")

    async def subscribe(self, client_id: str, symbol: str):
        """Subscribe a client to a trading pair"""
        if client_id not in self.subscriptions:
            return
        
        if symbol not in self.subscriptions[client_id]:
            self.subscriptions[client_id].append(symbol)
            
            if symbol not in self.symbol_subscribers:
                self.symbol_subscribers[symbol] = []
            self.symbol_subscribers[symbol].append(client_id)
            
            self.logger.info(f"Client {client_id} subscribed to {symbol}")

    async def unsubscribe(self, client_id: str, symbol: str):
        """Unsubscribe a client from a trading pair"""
        if client_id in self.subscriptions and symbol in self.subscriptions[client_id]:
            self.subscriptions[client_id].remove(symbol)
            if symbol in self.symbol_subscribers:
                self.symbol_subscribers[symbol].remove(client_id)
                if not self.symbol_subscribers[symbol]:
                    del self.symbol_subscribers[symbol]
            self.logger.info(f"Client {client_id} unsubscribed from {symbol}")

    async def broadcast_price(self, symbol: str, price: float, timestamp: Optional[datetime] = None):
        """Broadcast price update to all subscribed clients"""
        if not timestamp:
            timestamp = datetime.utcnow()
            
        self.last_prices[symbol] = price
        message = {
            "type": "price_update",
            "symbol": symbol,
            "price": price,
            "timestamp": timestamp.isoformat()
        }
        
        if symbol in self.symbol_subscribers:
            for client_id in self.symbol_subscribers[symbol]:
                if client_id in self.connections:
                    try:
                        await self.connections[client_id].send(json.dumps(message))
                    except websockets.exceptions.ConnectionClosed:
                        await self.unregister(client_id)
                    except Exception as e:
                        self.logger.error(f"Error sending to client {client_id}: {str(e)}")

    async def broadcast_orderbook(self, symbol: str, bids: List[List[float]], asks: List[List[float]]):
        """Broadcast orderbook update to all subscribed clients"""
        message = {
            "type": "orderbook_update",
            "symbol": symbol,
            "bids": bids,
            "asks": asks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if symbol in self.symbol_subscribers:
            for client_id in self.symbol_subscribers[symbol]:
                if client_id in self.connections:
                    try:
                        await self.connections[client_id].send(json.dumps(message))
                    except websockets.exceptions.ConnectionClosed:
                        await self.unregister(client_id)
                    except Exception as e:
                        self.logger.error(f"Error sending to client {client_id}: {str(e)}")

    async def handle_client_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Handle incoming client messages"""
        try:
            data = json.loads(message)
            client_id = str(id(websocket))
            
            if data["type"] == "subscribe":
                await self.subscribe(client_id, data["symbol"])
                
            elif data["type"] == "unsubscribe":
                await self.unsubscribe(client_id, data["symbol"])
                
            elif data["type"] == "get_last_price":
                symbol = data["symbol"]
                if symbol in self.last_prices:
                    response = {
                        "type": "last_price",
                        "symbol": symbol,
                        "price": self.last_prices[symbol],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send(json.dumps(response))
                    
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message received: {message}")
        except KeyError as e:
            self.logger.error(f"Missing required field in message: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")

    async def start_server(self, host: str = 'localhost', port: int = 8765):
        """Start the WebSocket server"""
        async def handler(websocket: websockets.WebSocketServerProtocol, path: str):
            client_id = await self.register(websocket)
            try:
                async for message in websocket:
                    await self.handle_client_message(websocket, message)
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                await self.unregister(client_id)

        self.logger.info(f"Starting WebSocket server on ws://{host}:{port}")
        async with websockets.serve(handler, host, port):
            await asyncio.Future()  # run forever

# Example usage:
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start WebSocket manager
    manager = WebSocketManager()
    asyncio.run(manager.start_server())
