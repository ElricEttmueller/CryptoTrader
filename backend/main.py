from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import ccxt
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import sys
import os
import pandas as pd
from urllib.parse import unquote
from datetime import timedelta

# Add backend to path
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.utils.websocket_manager import WebSocketManager
from backend.utils.market_data_service import MarketDataService
from backend.trading.order_manager import OrderManager, OrderType, OrderSide
from backend.trading.risk_manager import RiskManager
from backend.trading.portfolio_manager import PortfolioManager
from backend.database.db_config import DatabaseManager
from backend.routes.trading_routes import router as trading_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CryptoTrader API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trading_router, prefix="/api")

# Initialize managers
websocket_manager = WebSocketManager()
market_data_service = MarketDataService(websocket_manager=websocket_manager)

# Initialize exchange
exchange = ccxt.binance({
    'apiKey': os.getenv('EXCHANGE_API_KEY'),
    'secret': os.getenv('EXCHANGE_API_SECRET'),
    'enableRateLimit': True,
})

order_manager = OrderManager(exchange=exchange)
risk_manager = RiskManager(order_manager=order_manager)
portfolio_manager = PortfolioManager(order_manager=order_manager, risk_manager=risk_manager)
db = DatabaseManager()

@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    await db.connect()
    logger.info("Database connection established")
    
    # Initialize exchange in test mode
    exchange.apiKey = os.getenv('EXCHANGE_API_KEY')
    exchange.secret = os.getenv('EXCHANGE_API_SECRET')
    exchange.set_sandbox_mode(True)  # Enable sandbox/test mode
    
    # Start market data service
    await market_data_service.start()
    logger.info("Market data service started")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await market_data_service.stop()
    await db.close()
    logger.info("Services stopped")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"status": "online", "service": "CryptoTrader API"}

@app.get("/markets")
async def get_markets():
    """Get available markets."""
    try:
        # Return some common trading pairs for testing
        test_markets = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", 
            "SOL/USDT", "XRP/USDT", "DOT/USDT", "DOGE/USDT"
        ]
        return {"markets": test_markets}
    except Exception as e:
        logger.error(f"Error getting markets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/live-data/{pair}")
async def get_live_data(pair: str):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        ticker = exchange.fetch_ticker(decoded_pair)
        ohlcv = exchange.fetch_ohlcv(decoded_pair, '1m', limit=60)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        price_data = {
            'current_price': ticker['last'],
            'high_24h': ticker['high'],
            'low_24h': ticker['low'],
            'volume_24h': ticker['quoteVolume'],
            'price_change_24h': ticker['percentage'],
            'chart_data': {
                'timestamps': df['timestamp'].dt.strftime('%H:%M').tolist(),
                'prices': df['close'].tolist(),
            }
        }
        
        return price_data
    except Exception as e:
        logger.error(f"Error fetching price data: {str(e)}")
        return {"error": str(e)}

@app.get("/orderbook/{pair}")
async def get_orderbook(pair: str):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        orderbook = exchange.fetch_order_book(decoded_pair, limit=10)
        return {
            "bids": orderbook['bids'],
            "asks": orderbook['asks']
        }
    except Exception as e:
        logger.error(f"Error fetching orderbook: {str(e)}")
        return {"error": str(e)}

@app.get("/trades/{pair}")
async def get_recent_trades(pair: str):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        trades = exchange.fetch_trades(decoded_pair, limit=50)
        return {
            "trades": [
                {
                    "time": trade['datetime'],
                    "price": trade['price'],
                    "amount": trade['amount'],
                    "side": trade['side']
                }
                for trade in trades
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching trades: {str(e)}")
        return {"error": str(e)}

@app.get("/historical-data/{pair}")
async def get_historical_data(
    pair: str,
    timeframe: str = "1d",
    limit: int = 100,
    since: str = None,
):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        
        # Validate timeframe
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M']
        if timeframe not in valid_timeframes:
            return {"error": f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"}
            
        # Convert since parameter to timestamp
        start_time = None
        if since:
            try:
                start_time = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                return {"error": "Invalid since parameter. Must be ISO format (e.g., '2024-03-19T00:00:00Z')"}
        else:
            start_time = datetime.utcnow() - timedelta(days=limit)
        
        # Try to get data from database first
        historical_data = await db.get_historical_data(
            symbol=decoded_pair,
            timeframe=timeframe,
            start_time=start_time
        )
        
        # If no data in database or data is old, fetch from exchange
        if not historical_data or (
            historical_data[-1]["timestamp"] < datetime.utcnow() - timedelta(minutes=5)
        ):
            ohlcv = exchange.fetch_ohlcv(
                decoded_pair,
                timeframe=timeframe,
                limit=limit,
                since=int(start_time.timestamp() * 1000) if start_time else None
            )
            
            # Save to database
            await db.save_historical_data(decoded_pair, timeframe, ohlcv)
            
            # Convert to DataFrame for processing
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
        else:
            # Convert database data to DataFrame
            df = pd.DataFrame(historical_data)
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculate additional metrics
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['rsi'] = calculate_rsi(df['close'])
        
        # Format response
        response_data = {
            'pair': decoded_pair,
            'timeframe': timeframe,
            'data': [
                {
                    'timestamp': row['timestamp'].isoformat(),
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume'],
                    'sma_20': row['sma_20'],
                    'sma_50': row['sma_50'],
                    'rsi': row['rsi']
                }
                for _, row in df.iterrows()
            ]
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return {"error": str(e)}

@app.post("/order/create/{pair}")
async def create_trade_order(
    pair: str,
    order_type: str,
    side: str,
    amount: float,
    price: Optional[float] = None,
    params: Optional[Dict] = None,
):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        
        # Validate order type
        try:
            order_type_enum = OrderType[order_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid order type. Must be one of: {[t.name for t in OrderType]}"
            )
            
        # Validate order side
        try:
            side_enum = OrderSide[side.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid order side. Must be one of: {[s.name for s in OrderSide]}"
            )
            
        order = await order_manager.create_order(
            symbol=decoded_pair,
            order_type=order_type_enum,
            side=side_enum,
            amount=amount,
            price=price,
            params=params
        )
        
        return {
            "status": "success",
            "order": order
        }
        
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/order/cancel/{pair}/{order_id}")
async def cancel_trade_order(pair: str, order_id: str):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        result = await order_manager.cancel_order(order_id, decoded_pair)
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error canceling order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/order/status/{pair}/{order_id}")
async def get_order_status(pair: str, order_id: str):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        order = await order_manager.get_order_status(order_id, decoded_pair)
        
        return {
            "status": "success",
            "order": order
        }
        
    except Exception as e:
        logger.error(f"Error fetching order status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/positions")
async def get_positions():
    try:
        positions = await order_manager.get_open_positions()
        
        return {
            "status": "success",
            "positions": positions
        }
        
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/position/{pair}")
async def get_position(pair: str):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        position = await order_manager.update_position(decoded_pair)
        risk_metrics = order_manager.get_position_risk(decoded_pair)
        
        return {
            "status": "success",
            "position": position,
            "risk_metrics": risk_metrics
        }
        
    except Exception as e:
        logger.error(f"Error fetching position: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/risk/position-size/{pair}")
async def calculate_position_size(
    pair: str,
    entry_price: float,
    stop_loss: float,
    portfolio_value: float,
    risk_level: Optional[str] = "MEDIUM",
):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        
        try:
            risk_level_enum = RiskLevel[risk_level.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid risk level. Must be one of: {[r.name for r in RiskLevel]}"
            )
        
        position_info = await risk_manager.calculate_position_size(
            symbol=decoded_pair,
            entry_price=entry_price,
            stop_loss=stop_loss,
            portfolio_value=portfolio_value,
            risk_level=risk_level_enum
        )
        
        return {
            "status": "success",
            "position_info": position_info
        }
        
    except Exception as e:
        logger.error(f"Error calculating position size: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/risk/stop-loss/{pair}")
async def set_stop_loss(
    pair: str,
    position_size: float,
    entry_price: float,
    stop_price: float,
    is_trailing: bool = False,
    callback_rate: Optional[float] = None,
):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        
        order = await risk_manager.set_stop_loss(
            symbol=decoded_pair,
            position_size=position_size,
            entry_price=entry_price,
            stop_price=stop_price,
            is_trailing=is_trailing,
            callback_rate=callback_rate
        )
        
        return {
            "status": "success",
            "stop_loss_order": order
        }
        
    except Exception as e:
        logger.error(f"Error setting stop loss: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/risk/take-profit/{pair}")
async def set_take_profit(
    pair: str,
    position_size: float,
    entry_price: float,
    profit_targets: List[Dict[str, float]],
):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        
        orders = await risk_manager.set_take_profit(
            symbol=decoded_pair,
            position_size=position_size,
            entry_price=entry_price,
            profit_targets=profit_targets
        )
        
        return {
            "status": "success",
            "take_profit_orders": orders
        }
        
    except Exception as e:
        logger.error(f"Error setting take profit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk/metrics/{pair}")
async def get_risk_metrics(pair: str):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        
        # Fetch historical prices for risk calculations
        ohlcv = exchange.fetch_ohlcv(decoded_pair, '1h', limit=100)
        prices = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])['close']
        
        # Get current positions
        positions = await order_manager.get_open_positions()
        position_dict = {pos["symbol"]: pos for pos in positions}
        
        metrics = risk_manager.calculate_risk_metrics(prices, position_dict)
        
        return {
            "status": "success",
            "risk_metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk/portfolio-limits")
async def check_portfolio_limits(portfolio_value: float):
    try:
        limits = await risk_manager.check_portfolio_limits(portfolio_value)
        
        return {
            "status": "success",
            "portfolio_limits": limits
        }
        
    except Exception as e:
        logger.error(f"Error checking portfolio limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/risk/adjust-position/{pair}")
async def adjust_position(
    pair: str,
    volatility_change: float,
):
    try:
        decoded_pair = unquote(pair).replace('-', '/')
        
        adjustment = await risk_manager.adjust_position_sizes(
            symbol=decoded_pair,
            volatility_change=volatility_change
        )
        
        return {
            "status": "success",
            "position_adjustment": adjustment
        }
        
    except Exception as e:
        logger.error(f"Error adjusting position: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/summary")
async def get_portfolio_summary(user_id: str):
    """Get current portfolio summary including positions and allocations."""
    try:
        summary = await portfolio_manager.get_portfolio_summary()
        
        # Save portfolio snapshot to database
        await db.save_portfolio_snapshot(user_id, summary)
        
        return {
            "status": "success",
            "portfolio": summary
        }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/allocations")
async def set_portfolio_allocations(
    allocations: Dict[str, float],
):
    """Set target allocations for portfolio assets."""
    try:
        result = await portfolio_manager.set_target_allocations(allocations)
        return {
            "status": "success",
            "result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting allocations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/rebalance")
async def rebalance_portfolio():
    """Rebalance portfolio to match target allocations."""
    try:
        orders = await portfolio_manager.rebalance_portfolio()
        return {
            "status": "success",
            "rebalance_orders": orders
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/metrics")
async def get_portfolio_metrics(
    timeframe: str = "1d",
    lookback_periods: int = 30,
):
    """Get portfolio performance metrics."""
    try:
        metrics = await portfolio_manager.calculate_portfolio_metrics(
            timeframe=timeframe,
            lookback_periods=lookback_periods
        )
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error calculating portfolio metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/markets")
async def get_markets():
    """Get available trading pairs"""
    return await market_data_service.get_available_symbols()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time market data"""
    await websocket.accept()
    client_id = await websocket_manager.register(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            if data['action'] == 'subscribe':
                symbol = data['symbol']
                await websocket_manager.subscribe(client_id, symbol)
                await market_data_service.start_price_updates(symbol)
                await market_data_service.start_orderbook_updates(symbol)
            elif data['action'] == 'unsubscribe':
                symbol = data['symbol']
                await websocket_manager.unsubscribe(client_id, symbol)
                await market_data_service.stop_price_updates(symbol)
                await market_data_service.stop_orderbook_updates(symbol)
    except WebSocketDisconnect:
        await websocket_manager.unregister(client_id)
    except Exception as e:
        logger.error(f"Error in websocket connection: {e}")
        await websocket_manager.unregister(client_id)

@app.post("/api/subscribe/{symbol}")
async def subscribe_market(symbol: str):
    """Start real-time updates for a symbol"""
    await market_data_service.start_price_updates(symbol)
    await market_data_service.start_orderbook_updates(symbol)
    return {"status": "success", "message": f"Subscribed to {symbol}"}

@app.post("/api/unsubscribe/{symbol}")
async def unsubscribe_market(symbol: str):
    """Stop real-time updates for a symbol"""
    await market_data_service.stop_price_updates(symbol)
    return {"status": "success", "message": f"Unsubscribed from {symbol}"}

def calculate_rsi(prices, periods=14):
    """Calculate Relative Strength Index."""
    deltas = prices.diff()
    gain = (deltas.where(deltas > 0, 0)).rolling(window=periods).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=periods).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
