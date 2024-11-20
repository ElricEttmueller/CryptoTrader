import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Add backend to path
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from utils.data_loader import DataLoader

def create_features(df):
    """Create basic technical indicators"""
    df['returns'] = df['close'].pct_change()
    df['sma_5'] = df['close'].rolling(window=5).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['rsi'] = calculate_rsi(df['close'])
    df['volatility'] = df['returns'].rolling(window=20).std()
    return df.dropna()

def calculate_rsi(prices, period=14):
    """Calculate RSI technical indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def prepare_data(df):
    """Prepare features and target for ML model"""
    features = ['sma_5', 'sma_20', 'rsi', 'volatility', 'returns']
    X = df[features]
    y = df['close'].shift(-1)  # Predict next day's close price
    return X[:-1], y[:-1]  # Remove last row since we don't have next day's price

def train_model():
    """Train and save ML model"""
    # Load historical data
    data_loader = DataLoader()
    df = data_loader.get_historical_data("BTC/USDT", "1h", limit=5000)
    
    # Prepare features
    df = create_features(df)
    X, y = prepare_data(df)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    
    # Save model and scaler
    model_path = Path(__file__).parent.parent / 'models'
    model_path.mkdir(exist_ok=True)
    
    joblib.dump(model, model_path / 'ml_trading_model.joblib')
    joblib.dump(scaler, model_path / 'feature_scaler.joblib')
    print("Model and scaler saved successfully!")

if __name__ == "__main__":
    train_model()
