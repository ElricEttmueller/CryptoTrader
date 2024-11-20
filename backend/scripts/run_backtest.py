import sys
import os
import logging
import asyncio
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.strategies.adaptive_strategy import AdaptiveStrategy
from backend.strategies.ml_strategy import MLTradingStrategy
from backend.strategies.ma_strategy import MovingAverageStrategy
from backend.strategies.rl_strategy import RLTradingStrategy
from backend.backtesting.engine import BacktestEngine

async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize strategies
    ml_strategy = MLTradingStrategy()
    ma_strategy = MovingAverageStrategy()
    rl_strategy = RLTradingStrategy()
    
    # Initialize adaptive strategy
    strategy = AdaptiveStrategy(ml_strategy, ma_strategy, rl_strategy)
    
    # Initialize backtest engine
    use_live_data = os.getenv('USE_LIVE_DATA', 'false').lower() == 'true'
    engine = BacktestEngine(
        initial_capital=10000,  # Starting with $10,000
        use_live_data=use_live_data
    )
    
    # Set backtest parameters
    symbol = "BTC/USDT"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")  # Last 30 days
    
    # Run backtest
    logging.info(f"Running backtest for {symbol} from {start_date} to {end_date}")
    logging.info(f"Using {'live' if use_live_data else 'synthetic'} data")
    
    results = await engine.run_backtest(strategy, symbol, start_date, end_date)
    
    if results:
        # Print results
        logging.info("\nBacktest Results:")
        logging.info(f"Final Portfolio Value: ${results['final_portfolio_value']:.2f}")
        logging.info(f"Total Return: {results['total_return']:.2f}%")
        logging.info(f"Number of Trades: {len(results['trades'])}")
        
        # Plot results
        await engine.plot_results(results)
    else:
        logging.error("Backtest failed to generate results")

if __name__ == "__main__":
    asyncio.run(main())
