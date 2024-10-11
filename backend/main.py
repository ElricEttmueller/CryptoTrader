from fastapi import FastAPI
import ccxt
import logging
from urllib.parse import unquote


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

for route in app.routes:
    print(f"Route path: {route.path}, methods: {route.methods}")
