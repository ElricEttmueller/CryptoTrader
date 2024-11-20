import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from .base_strategy import BaseStrategy
from .ml_strategy import MLTradingStrategy
from .ma_strategy import MovingAverageStrategy
from .rl_strategy import RLTradingStrategy
import ta
import logging

class MarketRegime:
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    BREAKOUT = "BREAKOUT"
    REVERSAL = "REVERSAL"

class AdaptiveStrategy(BaseStrategy):
    def __init__(self, ml_strategy, ma_strategy, rl_strategy):
        """
        Initialize adaptive trading strategy with ML, MA, and RL strategies
        """
        super().__init__('Adaptive Multi-Strategy')
        
        self.ml_strategy = ml_strategy
        self.ma_strategy = ma_strategy
        self.rl_strategy = rl_strategy
        self.lookback_period = 20
        
        # Initial strategy weights for different market regimes
        self.regime_strategy_weights = {
            MarketRegime.TRENDING_UP: {'ml': 0.3, 'ma': 0.4, 'rl': 0.3},
            MarketRegime.TRENDING_DOWN: {'ml': 0.3, 'ma': 0.4, 'rl': 0.3},
            MarketRegime.RANGING: {'ml': 0.4, 'ma': 0.2, 'rl': 0.4},
            MarketRegime.VOLATILE: {'ml': 0.3, 'ma': 0.3, 'rl': 0.4},
            MarketRegime.BREAKOUT: {'ml': 0.4, 'ma': 0.3, 'rl': 0.3},
            MarketRegime.REVERSAL: {'ml': 0.4, 'ma': 0.2, 'rl': 0.4}
        }
        
        # Strategy performance tracking
        self.strategy_performance = {
            'ml': {'correct': 0, 'total': 0, 'pnl': [], 'duration': []},
            'ma': {'correct': 0, 'total': 0, 'pnl': [], 'duration': []},
            'rl': {'correct': 0, 'total': 0, 'pnl': [], 'duration': []}
        }
        
        # Dynamic parameters
        self.volatility_window = 50  
        self.volatility_percentile = 70  
        self.trend_strength_window = 50  
        self.trend_strength_percentile = 70  
        
        # Performance tracking
        self.base_performance_window = 30  
        self.performance_window = self.base_performance_window
        self.performance_history = []
        
        # Risk management 
        self.min_strategy_weight = 0.2  
        self.base_risk_per_trade = 0.02  
        self.max_risk_per_trade = 0.04   
        self.stop_loss_atr_factor = 2.5  
        self.take_profit_atr_factor = 4.0 

    def update_strategy_weights(self, regime: str):
        """
        Update strategy weights based on recent performance
        """
        if len(self.performance_history) < self.performance_window:
            return
        
        # Calculate success rates
        success_rates = {}
        for strategy in ['ml', 'ma', 'rl']:
            perf = self.strategy_performance[strategy]
            success_rate = perf['correct'] / perf['total'] if perf['total'] > 0 else 0
            success_rates[strategy] = max(success_rate, self.min_strategy_weight)
        
        # Normalize weights
        total_success = sum(success_rates.values())
        if total_success > 0:
            for strategy in success_rates:
                success_rates[strategy] /= total_success
        
        # Update weights while maintaining minimum weight
        self.regime_strategy_weights[regime] = success_rates
    
    def update_performance(self, signals: Dict[str, pd.Series], actual_returns: pd.Series):
        """
        Update strategy performance metrics
        """
        for strategy, signal in signals.items():
            correct_predictions = ((signal * actual_returns) > 0).sum()
            total_predictions = len(actual_returns)
            
            self.strategy_performance[strategy]['correct'] += correct_predictions
            self.strategy_performance[strategy]['total'] += total_predictions
            
            # Keep only recent performance
            if self.strategy_performance[strategy]['total'] > self.performance_window:
                old_correct = self.strategy_performance[strategy]['correct']
                old_total = self.strategy_performance[strategy]['total']
                decay_factor = self.performance_window / old_total
                
                self.strategy_performance[strategy]['correct'] = int(old_correct * decay_factor)
                self.strategy_performance[strategy]['total'] = self.performance_window
                
            # Update PnL and duration
            self.strategy_performance[strategy]['pnl'].append(actual_returns.sum())
            self.strategy_performance[strategy]['duration'].append(len(actual_returns))
    
    def calculate_dynamic_thresholds(self, data: pd.DataFrame) -> Dict:
        """
        Calculate dynamic thresholds based on recent market conditions
        """
        if len(data) < self.volatility_window:
            return {
                'volatility': 1.5,
                'trend_strength': 25,
                'range': 0.03,
                'volume': 1.0
            }
        
        # Calculate rolling volatility with dynamic window
        returns = data['close'].pct_change()
        volatility = returns.rolling(window=self.lookback_period).std() * np.sqrt(365)
        vol_window = max(20, int(self.volatility_window * (1 + volatility.mean())))
        rolling_vol = returns.rolling(window=vol_window).std() * np.sqrt(365)
        
        # Dynamic percentile based on market conditions
        vol_percentile = min(85, max(65, self.volatility_percentile * (1 + volatility.mean())))
        vol_threshold = rolling_vol.quantile(vol_percentile/100)
        
        # Calculate rolling ADX with dynamic window
        trend_window = max(20, int(self.trend_strength_window * (1 - volatility.mean())))
        adx = ta.trend.adx(data['high'], data['low'], data['close'], window=trend_window)
        trend_threshold = adx.quantile(self.trend_strength_percentile/100)
        
        # Calculate dynamic range threshold
        typical_range = (data['high'] - data['low']).rolling(window=self.lookback_period).mean() / data['close']
        range_threshold = typical_range.quantile(0.5)
        
        # Volume threshold
        volume_ma = data['volume'].rolling(window=self.lookback_period).mean()
        volume_threshold = volume_ma.quantile(0.75)
        
        return {
            'volatility': vol_threshold,
            'trend_strength': trend_threshold,
            'range': range_threshold,
            'volume': volume_threshold
        }
    
    def detect_market_regime(self, data: pd.DataFrame) -> str:
        """
        Detect the current market regime using dynamic thresholds
        """
        if len(data) < self.lookback_period * 2:
            return MarketRegime.RANGING
            
        df = data.tail(self.lookback_period * 2).copy()
        
        # Get dynamic thresholds
        thresholds = self.calculate_dynamic_thresholds(data)
        
        # Calculate indicators
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=self.lookback_period).std() * np.sqrt(365)
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=self.lookback_period)
        df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=self.lookback_period)
        df['rsi'] = ta.momentum.rsi(df['close'], window=self.lookback_period)
        
        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(window=self.lookback_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Market conditions
        current_volatility = df['volatility'].iloc[-1]
        current_adx = df['adx'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        current_volume_ratio = df['volume_ratio'].iloc[-1]
        price_range = (df['high'].max() - df['low'].min()) / df['close'].mean()
        
        # Bollinger Bands for breakout detection
        bollinger = ta.volatility.BollingerBands(df['close'], window=self.lookback_period)
        df['bb_upper'] = bollinger.bollinger_hband()
        df['bb_lower'] = bollinger.bollinger_lband()
        
        last_close = df['close'].iloc[-1]
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        
        # Enhanced regime classification with volume confirmation
        if current_volatility > thresholds['volatility']:
            if current_adx > thresholds['trend_strength'] and current_volume_ratio > 1.2:
                if current_rsi > 70:
                    return MarketRegime.TRENDING_UP
                elif current_rsi < 30:
                    return MarketRegime.TRENDING_DOWN
            return MarketRegime.VOLATILE
            
        if (last_close > bb_upper or last_close < bb_lower) and current_volume_ratio > 1.5:
            if abs(df['returns'].iloc[-1]) > df['returns'].std() * 2:
                return MarketRegime.BREAKOUT
                
        if price_range < thresholds['range'] and current_volume_ratio < 0.8:
            return MarketRegime.RANGING
            
        if ((current_rsi < 30 and current_adx < thresholds['trend_strength'] * 0.8) or \
            (current_rsi > 70 and current_adx < thresholds['trend_strength'] * 0.8)) and \
           current_volume_ratio > 1.2:
            return MarketRegime.REVERSAL
            
        return MarketRegime.RANGING
    
    def calculate_position_size(self, data: pd.DataFrame, regime: str) -> float:
        """
        Calculate adaptive position size based on market conditions
        """
        volatility = data['close'].pct_change().std() * np.sqrt(365)
        
        # Adjust risk based on volatility
        risk_multiplier = max(0.5, min(1.5, 1 / volatility))
        
        # Adjust risk based on regime
        regime_risk_factors = {
            MarketRegime.TRENDING_UP: 1.2,
            MarketRegime.TRENDING_DOWN: 0.8,
            MarketRegime.RANGING: 0.9,
            MarketRegime.VOLATILE: 0.7,
            MarketRegime.BREAKOUT: 1.1,
            MarketRegime.REVERSAL: 0.8
        }
        
        risk_per_trade = min(
            self.max_risk_per_trade,
            self.base_risk_per_trade * risk_multiplier * regime_risk_factors[regime]
        )
        
        return risk_per_trade
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals by combining multiple strategies with dynamic weights
        """
        try:
            if len(data) < self.lookback_period * 2:
                return pd.Series(0, index=data.index)

            # Get current regime
            regime = self.detect_market_regime(data)
            
            # Update strategy weights based on performance
            self.update_strategy_weights(regime)
            
            # Get current weights
            weights = self.regime_strategy_weights[regime]
            
            # Calculate ATR for stop loss and take profit
            atr = ta.volatility.average_true_range(data['high'], data['low'], data['close'], window=self.lookback_period)
            current_atr = atr.iloc[-1]
            
            # Store individual strategy signals
            strategy_signals = {}
            signals = pd.Series(0, index=data.index)
            
            # Generate and combine signals
            valid_signals = 0
            for strategy, weight in weights.items():
                if weight > 0:
                    try:
                        if strategy == 'ml':
                            strategy_signal = self.ml_strategy.generate_signals(data)
                        elif strategy == 'ma':
                            strategy_signal = self.ma_strategy.generate_signals(data)
                        else:  # rl
                            strategy_signal = self.rl_strategy.generate_signals(data)
                            
                        if strategy_signal is not None and not strategy_signal.empty:
                            strategy_signals[strategy] = strategy_signal
                            signals += weight * strategy_signal
                            valid_signals += 1
                            
                    except Exception as e:
                        logging.warning(f"{strategy.upper()} Strategy Error: {str(e)}")

            # Only generate signals if we have enough valid strategy signals
            if valid_signals < 2:  
                return pd.Series(0, index=data.index)

            # Update strategy performance
            if len(strategy_signals) > 0:
                actual_returns = data['close'].pct_change()
                self.update_performance(strategy_signals, actual_returns)

            # Calculate position size
            risk_per_trade = self.calculate_position_size(data, regime)
            
            # Set stop loss and take profit levels
            current_price = data['close'].iloc[-1]
            stop_loss = current_price * (1 - self.stop_loss_atr_factor * current_atr)
            take_profit = current_price * (1 + self.take_profit_atr_factor * current_atr)
            
            # Generate final signals with risk management
            signals = pd.Series(np.where(signals > 0.3, risk_per_trade,  
                                       np.where(signals < -0.3, -risk_per_trade, 0)),  
                              index=data.index)
            
            return signals
            
        except Exception as e:
            logging.error(f"Signal Generation Error: {str(e)}")
            return pd.Series(0, index=data.index)

    def get_current_regime_info(self, data: pd.DataFrame) -> Dict:
        """
        Get information about current market regime and strategy weights
        """
        try:
            if len(data) < self.lookback_period * 2:
                return {
                    'regime': MarketRegime.RANGING,
                    'strategy_weights': self.regime_strategy_weights[MarketRegime.RANGING],
                    'volatility': 0,
                    'trend_strength': 0,
                    'rsi': 50
                }
            
            regime = self.detect_market_regime(data)
            weights = self.regime_strategy_weights[regime]
            
            # Calculate metrics with proper window sizes
            volatility = data['close'].pct_change().rolling(window=self.lookback_period).std() * np.sqrt(365)
            adx = ta.trend.adx(data['high'], data['low'], data['close'], window=self.lookback_period)
            rsi = ta.momentum.rsi(data['close'], window=self.lookback_period)
            
            return {
                'regime': regime,
                'strategy_weights': weights,
                'volatility': volatility.iloc[-1] if not volatility.empty else 0,
                'trend_strength': adx.iloc[-1] if not adx.empty else 0,
                'rsi': rsi.iloc[-1] if not rsi.empty else 50
            }
            
        except Exception as e:
            logging.error(f"Data Error: {str(e)}")
            return {
                'regime': MarketRegime.RANGING,
                'strategy_weights': self.regime_strategy_weights[MarketRegime.RANGING],
                'volatility': 0,
                'trend_strength': 0,
                'rsi': 50
            }
