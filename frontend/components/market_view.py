import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import websockets
import json
import asyncio
from typing import Dict, List, Optional

class MarketView:
    def __init__(self, websocket_url: str = "ws://localhost:8000"):
        """Initialize Market View component"""
        self.websocket_url = websocket_url
        self.price_data: Dict[str, List[Dict]] = {}
        self.orderbook_data: Dict[str, Dict] = {}
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'selected_symbols' not in st.session_state:
            st.session_state.selected_symbols = []
        if 'price_history' not in st.session_state:
            st.session_state.price_history = {}
            
    async def connect_websocket(self):
        """Connect to WebSocket server"""
        while True:
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    st.success("Connected to market data service")
                    while True:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)
                            
                            if data['type'] == 'price_update':
                                self.handle_price_update(data)
                            elif data['type'] == 'orderbook_update':
                                self.handle_orderbook_update(data)
                        except websockets.exceptions.ConnectionClosed:
                            st.warning("WebSocket connection closed")
                            break
                        except json.JSONDecodeError as e:
                            st.error(f"Invalid message format: {e}")
                            continue
                        except Exception as e:
                            st.error(f"Error processing message: {e}")
                            continue
                            
            except (websockets.exceptions.ConnectionClosed, 
                    websockets.exceptions.InvalidStatusCode,
                    ConnectionRefusedError) as e:
                st.error(f"Connection error: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                st.error(f"Unexpected error: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            
    def handle_price_update(self, data: Dict):
        """Handle price update message"""
        symbol = data['symbol']
        if symbol not in self.price_data:
            self.price_data[symbol] = []
            
        self.price_data[symbol].append({
            'timestamp': datetime.fromisoformat(data['timestamp']),
            'price': data['price']
        })
        
        # Keep only last 100 data points
        if len(self.price_data[symbol]) > 100:
            self.price_data[symbol] = self.price_data[symbol][-100:]
            
    def handle_orderbook_update(self, data: Dict):
        """Handle orderbook update message"""
        self.orderbook_data[data['symbol']] = {
            'bids': data['bids'],
            'asks': data['asks'],
            'timestamp': datetime.fromisoformat(data['timestamp'])
        }
        
    def plot_price_chart(self, symbol: str):
        """Plot real-time price chart"""
        if symbol not in self.price_data or not self.price_data[symbol]:
            return
            
        df = pd.DataFrame(self.price_data[symbol])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines',
            name=symbol
        ))
        
        fig.update_layout(
            title=f"{symbol} Price",
            xaxis_title="Time",
            yaxis_title="Price",
            height=400,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def plot_orderbook(self, symbol: str):
        """Plot real-time orderbook"""
        if symbol not in self.orderbook_data:
            return
            
        data = self.orderbook_data[symbol]
        bids = pd.DataFrame(data['bids'], columns=['price', 'size'])
        asks = pd.DataFrame(data['asks'], columns=['price', 'size'])
        
        fig = go.Figure()
        
        # Plot bids
        fig.add_trace(go.Bar(
            x=bids['price'],
            y=bids['size'],
            name="Bids",
            marker_color='green'
        ))
        
        # Plot asks
        fig.add_trace(go.Bar(
            x=asks['price'],
            y=asks['size'],
            name="Asks",
            marker_color='red'
        ))
        
        fig.update_layout(
            title=f"{symbol} Orderbook",
            xaxis_title="Price",
            yaxis_title="Size",
            height=300,
            template="plotly_dark",
            barmode='overlay',
            bargap=0
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def render(self):
        """Render the market view component"""
        self.initialize_session_state()
        
        st.subheader("Market View")
        
        # Symbol selection
        symbols = st.multiselect(
            "Select Trading Pairs",
            options=['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],  # Replace with API call
            default=st.session_state.selected_symbols
        )
        
        if symbols != st.session_state.selected_symbols:
            st.session_state.selected_symbols = symbols
            
        # Create columns for different symbols
        if symbols:
            cols = st.columns(len(symbols))
            for col, symbol in zip(cols, symbols):
                with col:
                    st.markdown(f"### {symbol}")
                    self.plot_price_chart(symbol)
                    self.plot_orderbook(symbol)
                    
                    # Latest price
                    if symbol in self.price_data and self.price_data[symbol]:
                        latest_price = self.price_data[symbol][-1]['price']
                        st.metric(
                            "Latest Price",
                            f"${latest_price:,.2f}",
                            delta=None  # Add price change calculation
                        )
                        
    def run(self):
        """Run the market view component"""
        asyncio.run(self.connect_websocket())
