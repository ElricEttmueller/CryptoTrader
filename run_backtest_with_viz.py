import asyncio
from backend.backtesting.engine import BacktestEngine
from backend.strategies.ml_strategy import MLTradingStrategy
from backend.visualization.trading_viz import TradingVisualizer
import logging
from sklearn.metrics import confusion_matrix
import numpy as np
import pandas as pd
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_backtest():
    # Initialize components
    strategy = MLTradingStrategy(lookback_period=20)
    engine = BacktestEngine(initial_capital=10000, use_live_data=False)
    visualizer = TradingVisualizer()
    
    # Run backtest
    symbol = "BTC/USD"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    logging.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
    
    # Get price data
    price_data = await engine.fetch_data(symbol, start_date, end_date)
    
    # Generate features and train model
    df = strategy.generate_features(price_data)
    if not df.empty:
        train_size = int(len(df) * 0.8)
        train_data = df.iloc[:train_size]
        test_data = df.iloc[train_size:]
        
        # Train model and get predictions
        strategy.train_model(train_data)
        
        # Get ML metrics
        train_metrics = {
            'accuracy': strategy.model_accuracy,
            'feature_importance': dict(zip(strategy.feature_cols, strategy.model.feature_importances_)),
            'class_distribution': dict(df['target'].value_counts().items())
        }
        
        test_metrics = {
            'accuracy': strategy.test_accuracy,
            'class_distribution': dict(test_data['target'].value_counts().items()),
            'confusion_matrix': confusion_matrix(
                test_data['target'],
                strategy.model.predict(strategy.scaler.transform(test_data[strategy.feature_cols]))
            ).tolist()
        }
        
        # Generate signals
        signals = strategy.generate_signals(price_data)
        
        # Run backtest
        results = await engine.run_backtest(strategy, symbol, start_date, end_date)
        
        if results and results.get('trades'):
            # Create visualizations
            logging.info("Generating visualizations...")
            
            # Create visualization directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            viz_dir = f"visualizations/backtest_{timestamp}"
            os.makedirs(viz_dir, exist_ok=True)
            
            # 1. Trading Performance
            perf_fig = visualizer.plot_trading_performance(price_data, results['trades'])
            perf_fig.write_html(f"{viz_dir}/trading_performance.html")
            
            # 2. PnL Distribution
            pnl_fig = visualizer.plot_pnl_distribution(results['trades'])
            pnl_fig.write_html(f"{viz_dir}/pnl_distribution.html")
            
            # 3. Win Rate Analysis
            win_fig = visualizer.plot_win_rate_analysis(results['trades'])
            win_fig.write_html(f"{viz_dir}/win_rate_analysis.html")
            
            # 4. ML Metrics
            ml_fig = visualizer.plot_ml_metrics(train_metrics, test_metrics)
            ml_fig.write_html(f"{viz_dir}/ml_metrics.html")
            
            # 5. Trading Signals
            signals_fig = visualizer.plot_trading_signals(price_data, signals)
            signals_fig.write_html(f"{viz_dir}/trading_signals.html")
            
            # Save summary statistics to a text file
            trades_df = pd.DataFrame(results['trades'])
            sell_trades = trades_df[trades_df['side'] == 'sell']
            
            with open(f"{viz_dir}/summary.txt", "w") as f:
                f.write("=== Trading Performance Summary ===\n")
                f.write(f"Number of trades: {len(results['trades'])}\n")
                f.write(f"Total PnL: ${sum(trade.get('pnl', 0) for trade in results['trades']):.2f}\n")
                f.write(f"Win rate: {len(sell_trades[sell_trades['pnl'] > 0]) / len(sell_trades) * 100:.2f}%\n")
                f.write(f"Average winning trade: ${sell_trades[sell_trades['pnl'] > 0]['pnl'].mean():.2f}\n")
                f.write(f"Average losing trade: ${sell_trades[sell_trades['pnl'] <= 0]['pnl'].mean():.2f}\n")
                f.write(f"Largest winning trade: ${sell_trades['pnl'].max():.2f}\n")
                f.write(f"Largest losing trade: ${sell_trades['pnl'].min():.2f}\n")
                f.write(f"Final portfolio value: ${results['trades'][-1]['value']:.2f}\n")
            
            print("\n=== Trading Performance Summary ===")
            print(f"Number of trades: {len(results['trades'])}")
            print(f"Total PnL: ${sum(trade.get('pnl', 0) for trade in results['trades']):.2f}")
            print(f"Win rate: {len(sell_trades[sell_trades['pnl'] > 0]) / len(sell_trades) * 100:.2f}%")
            print(f"Average winning trade: ${sell_trades[sell_trades['pnl'] > 0]['pnl'].mean():.2f}")
            print(f"Average losing trade: ${sell_trades[sell_trades['pnl'] <= 0]['pnl'].mean():.2f}")
            print(f"Largest winning trade: ${sell_trades['pnl'].max():.2f}")
            print(f"Largest losing trade: ${sell_trades['pnl'].min():.2f}")
            print(f"Final portfolio value: ${results['trades'][-1]['value']:.2f}")
            print(f"\nVisualization files have been generated in: {viz_dir}/")
        else:
            logging.warning("No trades were generated during the backtest")

if __name__ == "__main__":
    asyncio.run(run_backtest())
