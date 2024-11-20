import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
import joblib
from pathlib import Path
from components.market_view import MarketView
from components.auth import AuthComponent

# Add backend to path
backend_path = str(Path(__file__).parent.parent / 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import strategies and utils
from strategies.ml_strategy import MLTradingStrategy
from strategies.adaptive_strategy import AdaptiveStrategy
from utils.data_loader import DataLoader

# Set page config
st.set_page_config(
    page_title="CryptoTrader ML Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize components
auth = AuthComponent()
market_view = MarketView(websocket_url="ws://localhost:8000/ws")

# Render authentication
auth.render()

# Only show trading interface if user is logged in
if st.session_state.user_token:
    # Load the ML model and scaler
    model_path = Path(__file__).parent.parent / 'backend' / 'models'
    try:
        model = joblib.load(model_path / 'ml_trading_model.joblib')
        scaler = joblib.load(model_path / 'feature_scaler.joblib')
        st.sidebar.success(" Model loaded successfully!")
    except Exception as e:
        st.sidebar.warning(" No model found. Training a new model...")
        try:
            from scripts.train_model import train_model
            train_model()
            model = joblib.load(model_path / 'ml_trading_model.joblib')
            scaler = joblib.load(model_path / 'feature_scaler.joblib')
            st.sidebar.success(" Model trained and loaded successfully!")
        except Exception as e:
            st.sidebar.error(f" Error training model: {str(e)}")
            model = None
            scaler = None

    def load_recent_data():
        """Load the most recent trading data"""
        try:
            data_loader = DataLoader()
            data = data_loader.get_historical_data("BTC/USDT", "1h", limit=1000)
            if data is not None and not data.empty:
                return data
            else:
                st.error("No data available")
                return None
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return None

    def plot_feature_importance(model, feature_names):
        """Plot feature importance"""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            fig = plt.figure(figsize=(10, 6))
            plt.bar(feature_names, importances)
            plt.xticks(rotation=45)
            plt.title("Feature Importance")
            plt.tight_layout()
            return fig
        return None

    def main():
        """Main dashboard function"""
        st.title("CryptoTrader ML Dashboard")
        
        # Sidebar
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Select Page",
            ["Market View", "ML Strategy", "Performance", "Model Overview", "Feature Analysis", "Live Predictions"]
        )
        
        # Add trading pairs selection
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
        selected_symbols = st.multiselect(
            "Select Trading Pairs",
            symbols,
            default=["BTC/USDT"]
        )
        
        if selected_symbols:
            st.session_state.selected_symbols = selected_symbols
            
        if page == "Market View":
            market_view.render()
            
        elif page == "ML Strategy":
            st.header("ML Strategy Configuration")
            # Add ML strategy configuration UI here
            
        elif page == "Performance":
            st.header("Performance Analytics")
            # Add performance analytics UI here
            
        elif page == "Model Overview":
            st.title("Model Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Model Information")
                if model is not None:
                    st.write(f"Model Type: {type(model).__name__}")
                    if hasattr(model, 'n_features_in_'):
                        st.write(f"Number of Features: {model.n_features_in_}")
                else:
                    st.warning("No model loaded")
                    
            with col2:
                st.subheader("Recent Performance")
                data = load_recent_data()
                if data is not None:
                    st.line_chart(data['close'])
                    
        elif page == "Feature Analysis":
            st.title("Feature Analysis")
            
            if model is not None and hasattr(model, 'feature_importances_'):
                feature_names = [f"Feature_{i}" for i in range(model.n_features_in_)]
                fig = plot_feature_importance(model, feature_names)
                if fig:
                    st.pyplot(fig)
            else:
                st.warning("Model does not support feature importance analysis")
                
        elif page == "Live Predictions":
            st.title("Live Predictions")
            
            if model is not None:
                data = load_recent_data()
                if data is not None:
                    # Process data and make predictions
                    st.subheader("Price Predictions")
                    st.line_chart(data['close'])
                    
                    # Add prediction logic here
                    st.info("Predictions will be implemented in the next update")
            else:
                st.warning("Please load a model to see predictions")

    if __name__ == "__main__":
        main()
        # Run WebSocket connection in background
        market_view.run()
else:
    st.info("Please login to access the trading dashboard")
