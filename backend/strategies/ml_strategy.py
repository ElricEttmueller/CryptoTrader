import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
from typing import Tuple, List
from .base_strategy import BaseStrategy
import ta
import logging

class MLTradingStrategy(BaseStrategy):
    def __init__(self, lookback_period: int = 20):
        """
        Initialize ML trading strategy
        """
        self.lookback_period = lookback_period
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model_accuracy = 0
        self.test_accuracy = 0
        self.scaler = StandardScaler()
        self.feature_cols = ['returns', 'log_returns', 'rsi', 'macd', 'adx', 'ma_ratio', 
                          'ema_ratio', 'atr', 'volatility', 'bb_width', 'volume_ratio',
                          'stoch_k', 'stoch_d', 'cci', 'higher_high', 'lower_low', 
                          'price_range', 'obv']
        
    def generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate features for ML model with improved NaN handling
        """
        try:
            if len(data) < self.lookback_period:
                return pd.DataFrame()
                
            df = data.copy()
            
            # Fill any missing values in the input data
            df = df.ffill().bfill()
            
            # Price features
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log1p(df['returns'])
            
            # Technical indicators - Trend
            df['rsi'] = ta.momentum.rsi(df['close'], window=14).fillna(50)
            df['macd'] = ta.trend.macd_diff(df['close']).fillna(0)
            df['adx'] = ta.trend.adx(df['high'], df['low'], df['close']).fillna(25)
            
            # Moving averages and crossovers
            df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20).ffill()
            df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50).ffill()
            df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12).ffill()
            df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26).ffill()
            
            # Handle division by zero in ratios
            df['ma_ratio'] = (df['sma_20'] / df['sma_50']).replace([np.inf, -np.inf], 1.0).fillna(1.0)
            df['ema_ratio'] = (df['ema_12'] / df['ema_26']).replace([np.inf, -np.inf], 1.0).fillna(1.0)
            
            # Volatility indicators
            df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close']).ffill()
            df['volatility'] = df['returns'].rolling(window=20).std().fillna(0)
            
            bb = ta.volatility.BollingerBands(df['close'])
            df['bb_upper'] = bb.bollinger_hband().ffill()
            df['bb_lower'] = bb.bollinger_lband().ffill()
            df['bb_width'] = ((df['bb_upper'] - df['bb_lower']) / df['close']).replace([np.inf, -np.inf], 0).fillna(0)
            
            # Volume features
            df['volume_ma'] = df['volume'].rolling(window=20).mean().ffill()
            df['volume_ratio'] = (df['volume'] / df['volume_ma']).replace([np.inf, -np.inf], 1.0).fillna(1.0)
            df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume']).fillna(0)
            
            # Momentum indicators
            df['stoch_k'] = ta.momentum.stoch(df['high'], df['low'], df['close']).fillna(50)
            df['stoch_d'] = ta.momentum.stoch_signal(df['high'], df['low'], df['close']).fillna(50)
            df['cci'] = ta.trend.cci(df['high'], df['low'], df['close']).fillna(0)
            
            # Price patterns
            df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
            df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
            df['price_range'] = ((df['high'] - df['low']) / df['close']).replace([np.inf, -np.inf], 0).fillna(0)
            
            # Target variable with multiple thresholds
            returns_std = df['returns'].std()
            if returns_std == 0:  # Handle the case where all returns are the same
                df['target'] = 2  # Neutral class
            else:
                future_returns = df['returns'].shift(-1).fillna(0)
                df['target'] = pd.qcut(future_returns, q=4, labels=[0, 1, 2, 3]).astype(int)
            
            # Ensure all features are finite
            for col in df.columns:
                df[col] = df[col].replace([np.inf, -np.inf], 0)
            
            # Drop the first few rows that might have NaN due to lookback periods
            df = df.iloc[self.lookback_period:]
            
            return df
            
        except Exception as e:
            logging.error(f"Error generating features: {str(e)}")
            return pd.DataFrame()
    
    def train_model(self, data: pd.DataFrame) -> None:
        """
        Train the ML model with improved methodology and overfitting prevention
        """
        try:
            logging.info("Generating features for ML model...")
            df = self.generate_features(data)
            if df.empty:
                logging.error("No features generated for training")
                return
            
            # Prepare features and target
            X = df[self.feature_cols].copy()
            y = df['target'].copy()
            
            # Check for NaN or infinite values
            if X.isna().any().any() or np.isinf(X).any().any():
                logging.warning("Found NaN or infinite values in features. Cleaning data...")
                X = X.replace([np.inf, -np.inf], np.nan)
                X = X.fillna(method='ffill').fillna(method='bfill')
            
            # Handle class imbalance
            logging.info("Computing class weights...")
            from sklearn.utils import class_weight
            class_weights = class_weight.compute_class_weight('balanced', 
                                                            classes=np.unique(y),
                                                            y=y)
            class_weight_dict = dict(zip(np.unique(y), class_weights))
            
            # Split data maintaining time order
            logging.info("Splitting data...")
            train_size = int(len(df) * 0.8)
            X_train = X[:train_size]
            y_train = y[:train_size]
            X_test = X[train_size:]
            y_test = y[train_size:]
            
            logging.info("Initializing and fitting scaler...")
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            logging.info("Initializing and training model...")
            # Initialize model with better parameters to prevent overfitting
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                min_samples_split=20,
                min_samples_leaf=10,
                max_features='sqrt',
                bootstrap=True,
                class_weight=class_weight_dict,
                random_state=42
            )
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Calculate accuracy
            self.model_accuracy = self.model.score(X_train_scaled, y_train)
            self.test_accuracy = self.model.score(X_test_scaled, y_test)
            
            logging.info(f"Model training complete - Train accuracy: {self.model_accuracy:.4f}, Test accuracy: {self.test_accuracy:.4f}")
            
            # Feature importance analysis
            importances = pd.DataFrame({
                'feature': self.feature_cols,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logging.info("\nTop 5 important features:")
            logging.info(importances.head())
            
            # Evaluate model performance per class
            from sklearn.metrics import classification_report
            y_pred = self.model.predict(X_test_scaled)
            logging.info("\nDetailed classification report:")
            logging.info("\n" + classification_report(y_test, y_pred))
            
            logging.info("Model training completed successfully")
            
        except Exception as e:
            logging.error(f"Error training model: {str(e)}")
            raise
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals using ML predictions with confidence thresholds
        """
        try:
            logging.info("Generating features for signal generation...")
            # Generate features
            df = self.generate_features(data)
            if df.empty:
                logging.warning("No features generated for signal generation")
                return pd.Series(0, index=data.index)
            
            # Prepare features
            X = df[self.feature_cols]
            
            # Check if model is trained
            if not hasattr(self, 'model') or not hasattr(self, 'scaler'):
                logging.warning("Model or scaler not initialized. Training now...")
                self.train_model(data)
                if not hasattr(self, 'model') or not hasattr(self, 'scaler'):
                    logging.error("Failed to initialize model or scaler after training")
                    return pd.Series(0, index=data.index)
                logging.info("Model and scaler initialized successfully")
            
            logging.info("Scaling features...")
            # Scale features
            try:
                X_scaled = self.scaler.transform(X)
                logging.info("Features scaled successfully")
            except Exception as e:
                logging.error(f"Error scaling features: {str(e)}")
                self.train_model(data)  # Retry training
                X_scaled = self.scaler.transform(X)
            
            # Get prediction probabilities
            logging.info("Generating predictions...")
            pred_proba = self.model.predict_proba(X_scaled)
            
            # Generate signals based on class probabilities with lower thresholds
            signals = pd.Series(0.0, index=df.index)  # Initialize as float
            
            # Strong sell signal (class 0)
            strong_sell = pred_proba[:, 0] > 0.3
            # Weak sell signal (class 1)
            weak_sell = pred_proba[:, 1] > 0.3
            # Weak buy signal (class 2)
            weak_buy = pred_proba[:, 2] > 0.3
            # Strong buy signal (class 3)
            strong_buy = pred_proba[:, 3] > 0.3
            
            # Set signals with confidence weighting
            signals[strong_sell] = -1.0
            signals[weak_sell] = -0.5
            signals[weak_buy] = 0.5
            signals[strong_buy] = 1.0
            
            # Add trend following bias
            trend = df['ma_ratio'].values - 1.0  # Above 1 means uptrend
            signals = signals + 0.2 * trend  # Add trend bias
            
            # Clip signals to [-1, 1] range
            signals = signals.clip(-1, 1)
            
            # Align signals with original data
            signals = signals.reindex(data.index, fill_value=0)
            
            logging.info(f"Generated {len(signals[signals != 0])} non-zero signals")
            return signals
            
        except Exception as e:
            logging.error(f"Error generating signals: {str(e)}")
            return pd.Series(0, index=data.index)
