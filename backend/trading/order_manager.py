from typing import Dict, Optional, List
import ccxt
import logging
from datetime import datetime
from decimal import Decimal
import asyncio
from enum import Enum

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    FAILED = "failed"

class OrderManager:
    def __init__(self, exchange: ccxt.Exchange):
        self.exchange = exchange
        self.open_orders: Dict[str, Dict] = {}
        self.positions: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        
    async def create_order(
        self,
        symbol: str,
        order_type: OrderType,
        side: OrderSide,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Create a new order on the exchange."""
        try:
            order_params = params or {}
            
            # Format the order parameters
            formatted_params = {
                "symbol": symbol,
                "type": order_type.value,
                "side": side.value,
                "amount": amount,
            }
            
            if price and order_type != OrderType.MARKET:
                formatted_params["price"] = price
                
            # Create the order
            order = await self.exchange.create_order(**formatted_params, **order_params)
            
            # Store the order in our local tracking
            self.open_orders[order["id"]] = {
                "order": order,
                "status": OrderStatus.OPEN,
                "created_at": datetime.now().isoformat(),
                "updates": []
            }
            
            self.logger.info(f"Created order: {order['id']} for {symbol}")
            return order
            
        except Exception as e:
            self.logger.error(f"Error creating order: {str(e)}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an existing order."""
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            
            if order_id in self.open_orders:
                self.open_orders[order_id]["status"] = OrderStatus.CANCELED
                self.open_orders[order_id]["updates"].append({
                    "timestamp": datetime.now().isoformat(),
                    "status": OrderStatus.CANCELED
                })
            
            self.logger.info(f"Canceled order: {order_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error canceling order: {str(e)}")
            raise

    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get the current status of an order."""
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            
            if order_id in self.open_orders:
                self.open_orders[order_id]["updates"].append({
                    "timestamp": datetime.now().isoformat(),
                    "status": order["status"]
                })
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error fetching order status: {str(e)}")
            raise

    async def update_position(self, symbol: str) -> Dict:
        """Update the current position for a symbol."""
        try:
            position = await self.exchange.fetch_position(symbol)
            
            if position:
                self.positions[symbol] = {
                    "amount": position["contracts"],
                    "entry_price": position["entryPrice"],
                    "unrealized_pnl": position["unrealizedPnl"],
                    "last_update": datetime.now().isoformat()
                }
            
            return self.positions.get(symbol, {})
            
        except Exception as e:
            self.logger.error(f"Error updating position: {str(e)}")
            raise

    async def get_open_positions(self) -> List[Dict]:
        """Get all current open positions."""
        try:
            positions = await self.exchange.fetch_positions()
            
            # Update our local position tracking
            for position in positions:
                if float(position["contracts"]) != 0:
                    symbol = position["symbol"]
                    self.positions[symbol] = {
                        "amount": position["contracts"],
                        "entry_price": position["entryPrice"],
                        "unrealized_pnl": position["unrealizedPnl"],
                        "last_update": datetime.now().isoformat()
                    }
            
            return [pos for pos in positions if float(pos["contracts"]) != 0]
            
        except Exception as e:
            self.logger.error(f"Error fetching positions: {str(e)}")
            raise

    def get_position_risk(self, symbol: str) -> Dict:
        """Calculate risk metrics for a position."""
        position = self.positions.get(symbol)
        if not position:
            return {}
            
        try:
            entry_price = float(position["entry_price"])
            amount = float(position["amount"])
            unrealized_pnl = float(position["unrealized_pnl"])
            
            return {
                "position_size": abs(amount),
                "entry_price": entry_price,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": (unrealized_pnl / (entry_price * abs(amount))) * 100 if amount != 0 else 0,
                "direction": "long" if amount > 0 else "short" if amount < 0 else "flat"
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating position risk: {str(e)}")
            return {}
