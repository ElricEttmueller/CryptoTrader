import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import plotly.express as px
from typing import List, Dict

class TradingVisualizer:
    def __init__(self):
        self.colors = {
            'buy': 'green',
            'sell': 'red',
            'profit': 'rgba(0, 255, 0, 0.2)',
            'loss': 'rgba(255, 0, 0, 0.2)',
        }

    def plot_trading_performance(self, price_data: pd.DataFrame, trades: List[Dict]) -> go.Figure:
        """
        Create an interactive plot showing price action and trades
        """
        # Convert trades to DataFrame
        trades_df = pd.DataFrame(trades)
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        
        # Create figure with secondary y-axis
        fig = make_subplots(rows=2, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.03,
                           row_heights=[0.7, 0.3],
                           subplot_titles=('Price Action & Trades', 'Portfolio Value'))

        # Add candlestick
        fig.add_trace(go.Candlestick(x=price_data.index,
                                    open=price_data['open'],
                                    high=price_data['high'],
                                    low=price_data['low'],
                                    close=price_data['close'],
                                    name='Price'),
                     row=1, col=1)

        # Add buy trades
        buy_trades = trades_df[trades_df['side'] == 'buy']
        fig.add_trace(go.Scatter(x=buy_trades['timestamp'],
                                y=buy_trades['price'],
                                mode='markers',
                                name='Buy',
                                marker=dict(symbol='triangle-up',
                                          size=10,
                                          color=self.colors['buy'])),
                     row=1, col=1)

        # Add sell trades
        sell_trades = trades_df[trades_df['side'] == 'sell']
        fig.add_trace(go.Scatter(x=sell_trades['timestamp'],
                                y=sell_trades['price'],
                                mode='markers',
                                name='Sell',
                                marker=dict(symbol='triangle-down',
                                          size=10,
                                          color=self.colors['sell'])),
                     row=1, col=1)

        # Add portfolio value
        fig.add_trace(go.Scatter(x=trades_df['timestamp'],
                                y=trades_df['value'],
                                mode='lines',
                                name='Portfolio Value',
                                line=dict(width=2)),
                     row=2, col=1)

        # Update layout
        fig.update_layout(
            title='Trading Performance',
            xaxis_title='Date',
            yaxis_title='Price',
            yaxis2_title='Portfolio Value',
            showlegend=True,
            height=800
        )

        return fig

    def plot_pnl_distribution(self, trades: List[Dict]) -> go.Figure:
        """
        Create a histogram of trade PnLs
        """
        trades_df = pd.DataFrame(trades)
        pnl_data = trades_df[trades_df['side'] == 'sell']['pnl']
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=pnl_data,
            nbinsx=50,
            name='PnL Distribution',
            marker_color=['red' if x < 0 else 'green' for x in pnl_data]
        ))
        
        fig.update_layout(
            title='PnL Distribution',
            xaxis_title='PnL',
            yaxis_title='Count',
            showlegend=False,
            bargap=0.1
        )
        
        return fig

    def plot_win_rate_analysis(self, trades: List[Dict]) -> go.Figure:
        """
        Create a comprehensive win rate analysis
        """
        trades_df = pd.DataFrame(trades)
        sell_trades = trades_df[trades_df['side'] == 'sell']
        
        # Calculate metrics
        total_trades = len(sell_trades)
        winning_trades = len(sell_trades[sell_trades['pnl'] > 0])
        losing_trades = len(sell_trades[sell_trades['pnl'] <= 0])
        win_rate = winning_trades / total_trades * 100
        
        avg_win = sell_trades[sell_trades['pnl'] > 0]['pnl'].mean()
        avg_loss = sell_trades[sell_trades['pnl'] <= 0]['pnl'].mean()
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Win Rate', 'Average Trade', 'Trade Count', 'Profit Factor'),
            specs=[[{'type': 'domain'}, {'type': 'bar'}],
                  [{'type': 'bar'}, {'type': 'indicator'}]]
        )
        
        # Win Rate Pie Chart
        fig.add_trace(go.Pie(
            labels=['Winning', 'Losing'],
            values=[winning_trades, losing_trades],
            marker_colors=['green', 'red']
        ), row=1, col=1)
        
        # Average Trade
        fig.add_trace(go.Bar(
            x=['Winning', 'Losing'],
            y=[avg_win, avg_loss],
            marker_color=['green', 'red']
        ), row=1, col=2)
        
        # Trade Count
        fig.add_trace(go.Bar(
            x=['Winning', 'Losing'],
            y=[winning_trades, losing_trades],
            marker_color=['green', 'red']
        ), row=2, col=1)
        
        # Profit Factor Gauge
        fig.add_trace(go.Indicator(
            mode='gauge+number',
            value=profit_factor,
            gauge={'axis': {'range': [0, max(3, profit_factor)]},
                  'steps': [
                      {'range': [0, 1], 'color': 'red'},
                      {'range': [1, 2], 'color': 'yellow'},
                      {'range': [2, 3], 'color': 'green'}
                  ]},
            title={'text': 'Profit Factor'}
        ), row=2, col=2)
        
        fig.update_layout(
            title='Trading Performance Analysis',
            showlegend=False,
            height=800
        )
        
        return fig

    def plot_ml_metrics(self, train_metrics: Dict, test_metrics: Dict) -> go.Figure:
        """
        Plot machine learning model metrics
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Model Accuracy', 'Feature Importance', 
                          'Class Distribution', 'Confusion Matrix'),
            specs=[[{'type': 'indicator'}, {'type': 'bar'}],
                  [{'type': 'pie'}, {'type': 'heatmap'}]]
        )
        
        # Accuracy Gauge
        fig.add_trace(go.Indicator(
            mode='gauge+number+delta',
            value=test_metrics['accuracy'] * 100,
            delta={'reference': train_metrics['accuracy'] * 100},
            gauge={'axis': {'range': [0, 100]},
                  'steps': [
                      {'range': [0, 33], 'color': 'red'},
                      {'range': [33, 66], 'color': 'yellow'},
                      {'range': [66, 100], 'color': 'green'}
                  ]},
            title={'text': 'Test Accuracy'}
        ), row=1, col=1)
        
        # Feature Importance
        fig.add_trace(go.Bar(
            x=list(train_metrics['feature_importance'].values())[:10],
            y=list(train_metrics['feature_importance'].keys())[:10],
            orientation='h',
            name='Feature Importance'
        ), row=1, col=2)
        
        # Class Distribution
        fig.add_trace(go.Pie(
            labels=list(test_metrics['class_distribution'].keys()),
            values=list(test_metrics['class_distribution'].values()),
            name='Class Distribution'
        ), row=2, col=1)
        
        # Confusion Matrix
        fig.add_trace(go.Heatmap(
            z=test_metrics['confusion_matrix'],
            x=['Pred ' + str(i) for i in range(len(test_metrics['confusion_matrix']))],
            y=['True ' + str(i) for i in range(len(test_metrics['confusion_matrix']))],
            colorscale='RdYlGn'
        ), row=2, col=2)
        
        fig.update_layout(
            title='Machine Learning Model Performance',
            showlegend=False,
            height=800
        )
        
        return fig

    def plot_trading_signals(self, data: pd.DataFrame, signals: pd.Series) -> go.Figure:
        """
        Plot trading signals overlaid on price
        """
        fig = make_subplots(rows=2, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.03,
                           row_heights=[0.7, 0.3],
                           subplot_titles=('Price & Signals', 'Signal Strength'))

        # Add price
        fig.add_trace(go.Candlestick(x=data.index,
                                    open=data['open'],
                                    high=data['high'],
                                    low=data['low'],
                                    close=data['close'],
                                    name='Price'),
                     row=1, col=1)

        # Add signals
        fig.add_trace(go.Scatter(x=signals.index,
                                y=signals,
                                mode='lines',
                                name='Signal Strength',
                                line=dict(width=1)),
                     row=2, col=1)

        # Add signal threshold lines
        fig.add_hline(y=0.3, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=-0.3, line_dash="dash", line_color="red", row=2, col=1)

        fig.update_layout(
            title='Trading Signals Analysis',
            xaxis_title='Date',
            yaxis_title='Price',
            yaxis2_title='Signal Strength',
            showlegend=True,
            height=800
        )

        return fig
