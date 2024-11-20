import asyncio
from backend.backtesting.engine import BacktestEngine
from backend.strategies.ml_strategy import MLTradingStrategy
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    # Initialize strategy and engine
    strategy = MLTradingStrategy(lookback_period=20)
    engine = BacktestEngine(initial_capital=10000, use_live_data=False)
    
    # Run backtest
    symbol = "BTC/USD"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    logging.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
    results = await engine.run_backtest(strategy, symbol, start_date, end_date)
    
    if results and results.get('trades'):
        logging.info(f"Number of trades: {len(results['trades'])}")
        
        # Calculate total PnL
        total_pnl = sum(trade.get('pnl', 0) for trade in results['trades'] if 'pnl' in trade)
        logging.info(f"Total PnL: ${total_pnl:.2f}")
        
        # Print final portfolio value
        final_value = results['trades'][-1]['value'] if results['trades'] else 10000
        returns_pct = ((final_value - 10000) / 10000) * 100
        logging.info(f"Final Portfolio Value: ${final_value:.2f}")
        logging.info(f"Total Return: {returns_pct:.2f}%")
    else:
        logging.warning("No trades were generated during the backtest")

if __name__ == "__main__":
    asyncio.run(main())
