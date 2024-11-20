from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from backtesting.engine import BacktestEngine
from strategies.adaptive_strategy import AdaptiveStrategy, MarketRegime
from strategies.ml_strategy import MLTradingStrategy
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rl_strategy import RLTradingStrategy
import numpy as np
import logging

def analyze_strategy_performance(results):
    """
    Analyze and visualize strategy performance
    """
    if not results or 'trades' not in results or not results['trades']:
        logging.warning("No trades were executed during the backtest period")
        return
        
    trades_df = pd.DataFrame(results['trades'])
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    trades_df.set_index('timestamp', inplace=True)
    
    # Calculate performance metrics
    total_trades = len(trades_df)
    profitable_trades = len(trades_df[trades_df['pnl'] > 0])
    win_rate = profitable_trades / total_trades if total_trades > 0 else 0
    
    total_pnl = trades_df['pnl'].sum()
    max_drawdown = calculate_max_drawdown(trades_df['cumulative_pnl'])
    
    logging.info("\nStrategy Performance Metrics:")
    logging.info(f"Total Trades: {total_trades}")
    logging.info(f"Profitable Trades: {profitable_trades}")
    logging.info(f"Win Rate: {win_rate:.2%}")
    logging.info(f"Total PnL: {total_pnl:.2f}")
    logging.info(f"Max Drawdown: {max_drawdown:.2%}")
    
    # Visualize trades and equity curve
    plot_trades(trades_df, results['prices'])

def plot_trades(trades_df, prices):
    """
    Plot trades and equity curve
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
    
    # Plot price
    fig.add_trace(
        go.Scatter(x=prices.index, y=prices['close'], name='Price'),
        row=1, col=1
    )
    
    # Plot buy and sell points
    buys = trades_df[trades_df['side'] == 'buy']
    sells = trades_df[trades_df['side'] == 'sell']
    
    fig.add_trace(
        go.Scatter(x=buys.index, y=buys['price'], mode='markers', name='Buy',
                  marker=dict(color='green', size=10)),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=sells.index, y=sells['price'], mode='markers', name='Sell',
                  marker=dict(color='red', size=10)),
        row=1, col=1
    )
    
    # Plot equity curve
    fig.add_trace(
        go.Scatter(x=trades_df.index, y=trades_df['cumulative_pnl'], name='Equity Curve'),
        row=2, col=1
    )
    
    fig.update_layout(
        title='Trading Strategy Performance',
        xaxis_title='Date',
        yaxis_title='Price',
        yaxis2_title='PnL'
    )
    
    fig.show()

def calculate_max_drawdown(equity_curve):
    """
    Calculate maximum drawdown from peak
    """
    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()

def calculate_sharpe_ratio(returns):
    """
    Calculate Sharpe ratio
    """
    risk_free_rate = 0.02  # Assuming 2% annual risk-free rate
    sharpe_ratio = (returns.mean() - risk_free_rate) / returns.std()
    return sharpe_ratio

def generate_synthetic_data(start_date, end_date, frequency='1d', trend_strength=0.5, volatility=0.02):
    """
    Generate synthetic price data for testing
    """
    # Convert dates to datetime
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Generate date range
    dates = pd.date_range(start=start, end=end, freq=frequency)
    n = len(dates)
    
    # Generate random walk with trend
    returns = np.random.normal(trend_strength/n, volatility, size=n)
    price = 100 * (1 + returns).cumprod()
    
    # Create DataFrame
    data = pd.DataFrame({
        'timestamp': dates,
        'open': price * (1 + np.random.normal(0, 0.001, n)),
        'high': price * (1 + abs(np.random.normal(0, 0.002, n))),
        'low': price * (1 - abs(np.random.normal(0, 0.002, n))),
        'close': price,
        'volume': np.random.lognormal(10, 1, n)
    })
    
    data.set_index('timestamp', inplace=True)
    return data

def test_adaptive_strategy():
    """
    Test the Adaptive strategy combining ML, MA, and RL approaches
    """
    # Initialize individual strategies
    ml_strategy = MLTradingStrategy(lookback_period=20)
    ma_strategy = MovingAverageStrategy(short_window=20, long_window=50)
    rl_strategy = RLTradingStrategy(lookback_period=20)
    
    # Initialize adaptive strategy
    adaptive_strategy = AdaptiveStrategy(
        ml_strategy=ml_strategy,
        ma_strategy=ma_strategy,
        rl_strategy=rl_strategy
    )
    
    # Generate synthetic data
    data = generate_synthetic_data(
        start_date='2023-01-01',
        end_date='2023-12-31',
        frequency='1d',
        trend_strength=0.6,
        volatility=0.02
    )
    
    print("\nTraining models...")
    
    # Train ML and RL models
    train_size = int(len(data) * 0.8)
    train_data = data.iloc[:train_size]
    
    ml_strategy.train_model(train_data)
    rl_strategy.train_model(train_data, total_timesteps=5000)
    
    # Initialize backtest engine
    engine = BacktestEngine(initial_capital=10000)
    
    # Run backtest
    results = engine.run_backtest(
        strategy=adaptive_strategy,
        symbol='BTC/USD',
        start_date='2023-01-01',
        end_date='2023-12-31'
    )
    
    if results:
        print("\nAdaptive Strategy Backtest Results:")
        print("-" * 50)
        print(f"Total Return: {results['total_return']:.2f}%")
        print(f"Final Portfolio Value: ${results['final_portfolio_value']:.2f}")
        print(f"Number of Trades: {len(results['trades'])}")
        
        if len(results['trades']) > 0:
            trades_df = pd.DataFrame(results['trades'])
            profitable_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df else 0
            total_trades = len(trades_df)
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
            print(f"Win Rate: {win_rate:.2f}%")

def test_ma_strategy():
    """
    Test the Moving Average strategy with different window combinations
    """
    # Initialize MA strategies with different window combinations
    ma_strategies = [
        {
            'name': 'MA(10,30)',
            'strategy': MovingAverageStrategy(short_window=10, long_window=30)
        },
        {
            'name': 'MA(20,50)',
            'strategy': MovingAverageStrategy(short_window=20, long_window=50)
        },
        {
            'name': 'MA(50,200)',
            'strategy': MovingAverageStrategy(short_window=50, long_window=200)
        }
    ]
    
    print("\nMoving Average Strategy Backtest Results:")
    print("-" * 50)
    
    for strat in ma_strategies:
        # Initialize backtest engine
        engine = BacktestEngine(initial_capital=10000)
        
        # Run backtest
        results = engine.run_backtest(
            strategy=strat['strategy'],
            symbol='BTC/USD',
            start_date='2023-01-01',
            end_date='2023-12-31'
        )
        
        if results:
            # Print results
            print(f"\nStrategy: {strat['name']}")
            print(f"Total Return: {results['total_return']:.2f}%")
            print(f"Final Portfolio Value: ${results['final_portfolio_value']:.2f}")
            print(f"Number of Trades: {len(results['trades'])}")
            
            # Calculate additional metrics
            if len(results['trades']) > 0:
                trades_df = pd.DataFrame(results['trades'])
                profitable_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df else 0
                total_trades = len(trades_df)
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                print(f"Win Rate: {win_rate:.2f}%")

def main():
    # Initialize strategies
    ml_strategy = MLTradingStrategy()
    ma_strategy = MovingAverageStrategy()
    adaptive_strategy = AdaptiveStrategy(ml_strategy, ma_strategy)
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # Set backtest parameters
    start_date = '2023-11-20'
    end_date = '2024-11-19'
    symbol = 'BTC/USDT'
    
    print(f"\nStarting Adaptive Strategy Backtest...")
    print(f"Testing period: {start_date} to {end_date}")
    
    # Run backtest
    results = engine.run_backtest(
        strategy=adaptive_strategy,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )
    
    # Analyze results
    if results:
        analyze_strategy_performance(results)

if __name__ == "__main__":
    # Run only MA strategy test
    test_ma_strategy()
