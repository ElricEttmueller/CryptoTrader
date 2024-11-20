import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from backend.strategies.adaptive_strategy import AdaptiveStrategy, MarketRegime
from backend.strategies.ml_strategy import MLTradingStrategy
from backend.strategies.ma_strategy import MovingAverageStrategy
from backend.strategies.rl_strategy import RLTradingStrategy

@pytest.fixture
def test_data():
    """Generate test market data"""
    periods = 200
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='1H')
    
    # Generate price data with known patterns
    base_price = 100
    trend = np.linspace(0, 20, periods)  # Upward trend
    volatility = np.random.normal(0, 1, periods)
    cycle = 10 * np.sin(np.linspace(0, 8*np.pi, periods))
    
    prices = base_price + trend + volatility + cycle
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.normal(0, 0.01, periods)),
        'high': prices * (1 + np.random.normal(0, 0.02, periods)),
        'low': prices * (1 - np.random.normal(0, 0.02, periods)),
        'close': prices,
        'volume': np.random.normal(1000, 200, periods)
    }).set_index('timestamp')
    
    return data

@pytest.fixture
def strategy():
    """Initialize adaptive strategy with mock sub-strategies"""
    ml_strategy = MLTradingStrategy()
    ma_strategy = MovingAverageStrategy()
    rl_strategy = RLTradingStrategy()
    return AdaptiveStrategy(ml_strategy, ma_strategy, rl_strategy)

def test_market_regime_detection(strategy, test_data):
    """Test market regime detection under different conditions"""
    # Test trending market
    trend_data = test_data.copy()
    trend_data['close'] = trend_data['close'] * 1.1  # Strong upward trend
    regime = strategy.detect_market_regime(trend_data)
    assert regime in [MarketRegime.TRENDING_UP, MarketRegime.BREAKOUT]
    
    # Test ranging market
    range_data = test_data.copy()
    range_data['close'] = 100 + np.random.normal(0, 0.5, len(test_data))  # Sideways movement
    regime = strategy.detect_market_regime(range_data)
    assert regime == MarketRegime.RANGING
    
    # Test volatile market
    volatile_data = test_data.copy()
    volatile_data['close'] = volatile_data['close'] * (1 + np.random.normal(0, 0.05, len(test_data)))
    regime = strategy.detect_market_regime(volatile_data)
    assert regime in [MarketRegime.VOLATILE, MarketRegime.BREAKOUT]

def test_strategy_weight_adaptation(strategy, test_data):
    """Test strategy weight adaptation based on performance"""
    # Initial weights
    initial_weights = strategy.regime_strategy_weights[MarketRegime.TRENDING_UP].copy()
    
    # Simulate good performance for ML strategy
    signals = {
        'ml': pd.Series(1, index=test_data.index),
        'ma': pd.Series(0, index=test_data.index),
        'rl': pd.Series(0, index=test_data.index)
    }
    returns = pd.Series(0.01, index=test_data.index)  # Positive returns
    
    # Update performance multiple times
    for _ in range(5):
        strategy.update_performance(signals, returns)
    
    # Update weights
    strategy.update_strategy_weights(MarketRegime.TRENDING_UP)
    
    # Check if ML strategy weight increased
    new_weights = strategy.regime_strategy_weights[MarketRegime.TRENDING_UP]
    assert new_weights['ml'] > initial_weights['ml']

def test_position_sizing(strategy, test_data):
    """Test adaptive position sizing"""
    # Test position size in different regimes
    regimes = [
        MarketRegime.TRENDING_UP,
        MarketRegime.TRENDING_DOWN,
        MarketRegime.VOLATILE,
        MarketRegime.RANGING
    ]
    
    sizes = [strategy.calculate_position_size(test_data, regime) for regime in regimes]
    
    # Check if position sizes are within bounds
    for size in sizes:
        assert strategy.min_strategy_weight <= size <= strategy.max_risk_per_trade
        
    # Volatile regime should have smaller position size
    volatile_size = strategy.calculate_position_size(test_data, MarketRegime.VOLATILE)
    trending_size = strategy.calculate_position_size(test_data, MarketRegime.TRENDING_UP)
    assert volatile_size < trending_size

def test_signal_generation(strategy, test_data):
    """Test signal generation and combination"""
    signals = strategy.generate_signals(test_data)
    
    # Check signal properties
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(test_data)
    assert all(abs(s) <= strategy.max_risk_per_trade for s in signals)
    
    # Test signal generation with insufficient data
    short_data = test_data.iloc[:10]
    short_signals = strategy.generate_signals(short_data)
    assert all(s == 0 for s in short_signals)

def test_regime_info(strategy, test_data):
    """Test regime info retrieval"""
    info = strategy.get_current_regime_info(test_data)
    
    # Check info structure
    assert 'regime' in info
    assert 'strategy_weights' in info
    assert 'volatility' in info
    assert 'trend_strength' in info
    assert 'rsi' in info
    
    # Check weight normalization
    weights = info['strategy_weights']
    assert abs(sum(weights.values()) - 1.0) < 0.0001
    
    # Test with insufficient data
    short_info = strategy.get_current_regime_info(test_data.iloc[:10])
    assert short_info['regime'] == MarketRegime.RANGING

def test_error_handling(strategy):
    """Test error handling with invalid data"""
    # Test with empty DataFrame
    empty_data = pd.DataFrame()
    signals = strategy.generate_signals(empty_data)
    assert len(signals) == 0
    
    # Test with invalid data types
    with pytest.raises(Exception):
        strategy.generate_signals(None)
    
    with pytest.raises(Exception):
        strategy.generate_signals([1, 2, 3])

def test_performance_tracking(strategy, test_data):
    """Test strategy performance tracking and metrics"""
    # Initial performance metrics
    initial_metrics = {
        strategy: strategy.strategy_performance.copy() 
        for strategy in ['ml', 'ma', 'rl']
    }
    
    # Simulate trades with known outcomes
    signals = {
        'ml': pd.Series([1, 1, -1, -1, 0] * 20, index=test_data.index[:100]),
        'ma': pd.Series([1, -1, 1, -1, 0] * 20, index=test_data.index[:100]),
        'rl': pd.Series([0, 1, -1, 1, -1] * 20, index=test_data.index[:100])
    }
    
    # Simulate returns matching signals
    returns = pd.Series([0.01, 0.01, -0.01, -0.01, 0] * 20, index=test_data.index[:100])
    
    # Update performance multiple times
    for _ in range(3):
        strategy.update_performance(signals, returns)
    
    # Check performance metrics
    for strat in ['ml', 'ma', 'rl']:
        perf = strategy.strategy_performance[strat]
        assert perf['total'] > initial_metrics[strat]['total']
        assert len(perf['pnl']) > len(initial_metrics[strat]['pnl'])
        assert len(perf['duration']) > len(initial_metrics[strat]['duration'])

def test_dynamic_parameters(strategy, test_data):
    """Test dynamic parameter adjustment based on market conditions"""
    # Test with different market conditions
    conditions = {
        'normal': test_data.copy(),
        'high_vol': test_data.copy(),
        'low_vol': test_data.copy()
    }
    
    # Modify data for different conditions
    conditions['high_vol']['close'] *= (1 + np.random.normal(0, 0.05, len(test_data)))
    conditions['low_vol']['close'] *= (1 + np.random.normal(0, 0.001, len(test_data)))
    
    thresholds = {}
    for condition, data in conditions.items():
        thresholds[condition] = strategy.calculate_dynamic_thresholds(data)
    
    # High volatility should have higher thresholds
    assert thresholds['high_vol']['volatility'] > thresholds['normal']['volatility']
    assert thresholds['low_vol']['volatility'] < thresholds['normal']['volatility']

def test_edge_cases(strategy):
    """Test strategy behavior with edge cases"""
    # Test with very small dataset
    tiny_data = pd.DataFrame({
        'open': [100, 101],
        'high': [102, 103],
        'low': [99, 98],
        'close': [101, 102],
        'volume': [1000, 1100]
    }, index=pd.date_range(end=datetime.now(), periods=2, freq='1H'))
    
    # Should return neutral signals
    signals = strategy.generate_signals(tiny_data)
    assert all(s == 0 for s in signals)
    
    # Test with extreme values
    extreme_data = pd.DataFrame({
        'open': [100, 1000],
        'high': [101, 1100],
        'low': [99, 900],
        'close': [100, 1000],
        'volume': [1000, 10000]
    }, index=pd.date_range(end=datetime.now(), periods=2, freq='1H'))
    
    # Should not crash and return valid signals
    signals = strategy.generate_signals(extreme_data)
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(extreme_data)
    
    # Test with missing values
    missing_data = test_data().copy()
    missing_data.loc[missing_data.index[10:15], 'close'] = np.nan
    
    # Should handle missing values gracefully
    info = strategy.get_current_regime_info(missing_data)
    assert isinstance(info, dict)
    assert 'regime' in info

if __name__ == '__main__':
    pytest.main(['-v'])
