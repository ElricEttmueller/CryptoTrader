from fastapi import FastAPI
import ccxt
import logging
from urllib.parse import unquote
from datetime import datetime


app = FastAPI()


logging.basicConfig(level=logging.INFO)



@app.get("/live-data/{pair:path}")
async def get_live_data(pair: str):
    decoded_pair = unquote(pair)
    logging.info(f"Decoded pair: {decoded_pair}")
    return {"pair_received": decoded_pair}


@app.get("/markets")
async def get_markets():
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    return {"available_markets": list(markets.keys())}



@app.get("/historical-data/{pair:path}")
async def get_historical_data(pair: str, timeframe: str = "1h", start_date: str = None, end_date: str = None):
    decoded_pair = unquote(pair)
    exchange = ccxt.binance()
    since = exchange.parse8601(start_date) if start_date else None
    until = exchange.parse8601(end_date) if end_date else None

    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol=decoded_pair,
            timeframe=timeframe,
            since=since,
            limit=1000
        )
        return {"pair": decoded_pair, "data": ohlcv}
    except Exception as e:
        logging.error(f"Error fetching historical data: {e}")
        return {"error": str(e)}


for route in app.routes:
    print(f"Route path: {route.path}, methods: {route.methods}")
