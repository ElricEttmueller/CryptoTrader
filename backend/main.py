from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import ccxt.async_support as ccxt_async 
import logging
from urllib.parse import unquote
from datetime import datetime
import logging
import asyncio
import ccxt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

@app.get("/live-data/{pair:path}")
async def get_live_data(pair: str):
    decoded_pair = unquote(pair)
    logging.info(f"Decoded pair: {decoded_pair}")
    return {"pair_received": decoded_pair}

@app.websocket("/ws/{pair:path}")
async def websocket_endpoint(websocket: WebSocket, pair: str):
    await websocket.accept()
    decoded_pair = unquote(pair)
    formatted_pair = decoded_pair
    exchange = ccxt_async.binance()
    try:
        while True:
            ticker = await exchange.fetch_ticker(formatted_pair)
            await websocket.send_json({
                'timestamp': ticker['timestamp'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
            })
            await asyncio.sleep(1)  # Adjust the interval as needed
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
    except Exception as e:
        logging.error(f"Error in WebSocket: {e}")
    finally:
        await exchange.close()
        await websocket.close()

@app.get("/markets")
async def get_markets():
    try:
        exchange = ccxt.binance()
        markets = exchange.load_markets()
        available_markets = list(markets.keys())
        logging.info(f"Markets fetched: {available_markets}")  # Log the markets fetched
        return {"available_markets": available_markets}
    except Exception as e:
        logging.error(f"Error loading markets: {e}")
        return {"error": str(e)}


@app.get("/historical-data/{pair:path}")
async def get_historical_data(pair: str, timeframe: str = "1h", start_date: str = None, end_date: str = None):
    decoded_pair = unquote(pair)
    formatted_pair = decoded_pair.replace('/', '')  # Convert 'BTC/USDT' to 'BTCUSDT'
    
    exchange = ccxt.binance()
    since = exchange.parse8601(start_date) if start_date else None
    until = exchange.parse8601(end_date) if end_date else None

    logging.info(f"Fetching historical data for pair: {formatted_pair}, timeframe: {timeframe}, since: {start_date}, until: {end_date}")

    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol=formatted_pair,
            timeframe=timeframe,
            since=since,
            limit=1000
        )
        logging.info(f"Data fetched for pair {formatted_pair}: {ohlcv}")
        return {"pair": formatted_pair, "data": ohlcv}
    except Exception as e:
        logging.error(f"Error fetching historical data: {e}")
        return {"error": str(e)}
