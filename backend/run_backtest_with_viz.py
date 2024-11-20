import argparse
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns

def create_features(df, feature_window):
    features = []
    for i in range(feature_window):
        df[f'close_lag_{i+1}'] = df['close'].shift(i+1)
        df[f'volume_lag_{i+1}'] = df['volume'].shift(i+1)
        features.extend([f'close_lag_{i+1}', f'volume_lag_{i+1}'])
    
    # Add technical indicators
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['rsi'] = calculate_rsi(df['close'])
    features.extend(['sma_20', 'sma_50', 'rsi'])
    
    return df, features

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def prepare_data(df, features, prediction_window, train_split):
    # Prepare features and target
    X = df[features].values
    y = df['close'].shift(-prediction_window).values
    
    # Remove rows with NaN values
    mask = ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    
    # Scale the data
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    X = scaler_X.fit_transform(X)
    y = scaler_y.fit_transform(y.reshape(-1, 1))
    
    # Split into train and test sets
    train_size = int(len(X) * train_split)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    return X_train, X_test, y_train, y_test, scaler_y

def create_model(input_shape, learning_rate):
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=input_shape),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(1)
    ])
    
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                 loss='mse',
                 metrics=['mae'])
    
    return model

def generate_visualizations(df, predictions, actual, trades, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    
    # Plot price predictions vs actual
    plt.figure(figsize=(12, 6))
    plt.plot(actual, label='Actual')
    plt.plot(predictions, label='Predicted')
    plt.title('Price Predictions vs Actual')
    plt.legend()
    plt.savefig(os.path.join(save_dir, 'predictions.png'))
    plt.close()
    
    # Plot PnL distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(trades['pnl'], bins=30)
    plt.title('PnL Distribution')
    plt.xlabel('PnL')
    plt.savefig(os.path.join(save_dir, 'pnl_distribution.png'))
    plt.close()
    
    # Save trade summary
    summary = f"""
    Number of Trades: {len(trades)}
    Win Rate: {(trades['pnl'] > 0).mean():.2%}
    Total PnL: ${trades['pnl'].sum():,.2f}
    Average Winning Trade: ${trades[trades['pnl'] > 0]['pnl'].mean():,.2f}
    Average Losing Trade: ${trades[trades['pnl'] < 0]['pnl'].mean():,.2f}
    Largest Winning Trade: ${trades['pnl'].max():,.2f}
    Largest Losing Trade: ${trades['pnl'].min():,.2f}
    Final Portfolio Value: ${trades['portfolio_value'].iloc[-1]:,.2f}
    """
    
    with open(os.path.join(save_dir, 'summary.txt'), 'w') as f:
        f.write(summary)

def main(args):
    # Load configuration
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # Load and prepare data
    # In a real implementation, this would fetch data from your data source
    # For now, we'll generate sample data
    dates = pd.date_range(start=args.start_date, end=args.end_date, freq=args.timeframe)
    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.normal(100, 10, len(dates)),
        'high': np.random.normal(105, 10, len(dates)),
        'low': np.random.normal(95, 10, len(dates)),
        'close': np.random.normal(100, 10, len(dates)),
        'volume': np.random.normal(1000000, 100000, len(dates))
    })
    
    # Create features
    df, features = create_features(df, config['feature_window'])
    
    # Prepare data for training
    X_train, X_test, y_train, y_test, scaler_y = prepare_data(
        df, features, config['prediction_window'], config['train_split']
    )
    
    # Create and train model
    model = create_model((len(features),), config['learning_rate'])
    model.fit(
        X_train, y_train,
        batch_size=config['batch_size'],
        epochs=config['epochs'],
        validation_split=0.2,
        verbose=0
    )
    
    # Make predictions
    predictions = model.predict(X_test)
    predictions = scaler_y.inverse_transform(predictions)
    actual = scaler_y.inverse_transform(y_test)
    
    # Simulate trading
    trades = pd.DataFrame({
        'timestamp': df.index[-len(predictions):],
        'predicted': predictions.flatten(),
        'actual': actual.flatten(),
        'position': np.where(predictions > actual, 1, -1),
        'pnl': np.zeros(len(predictions))
    })
    
    # Calculate PnL
    initial_balance = args.initial_balance
    trades['pnl'] = trades['position'] * (trades['actual'].shift(-1) - trades['actual'])
    trades['portfolio_value'] = initial_balance + trades['pnl'].cumsum()
    
    # Generate visualizations
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_dir = os.path.join('visualizations', f'backtest_{timestamp}')
    generate_visualizations(df, predictions.flatten(), actual.flatten(), trades, save_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, required=True)
    parser.add_argument('--start_date', type=str, required=True)
    parser.add_argument('--end_date', type=str, required=True)
    parser.add_argument('--initial_balance', type=float, required=True)
    parser.add_argument('--timeframe', type=str, required=True)
    parser.add_argument('--config', type=str, required=True)
    
    args = parser.parse_args()
    main(args)
