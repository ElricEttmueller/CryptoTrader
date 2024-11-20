from typing import Dict, List, Optional, Tuple
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .order_manager import OrderManager, OrderType, OrderSide
from .risk_manager import RiskManager

class PortfolioManager:
    def __init__(
        self,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        rebalance_threshold: float = 0.1,  # 10% deviation triggers rebalance
        min_position_size: float = 0.01,  # 1% minimum position size
        max_position_size: float = 0.3,  # 30% maximum position size
        risk_free_rate: float = 0.02  # 2% risk-free rate
    ):
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.rebalance_threshold = rebalance_threshold
        self.min_position_size = min_position_size
        self.max_position_size = max_position_size
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
        self.target_allocations: Dict[str, float] = {}
        
    async def get_portfolio_summary(self) -> Dict:
        """Get current portfolio positions and metrics."""
        try:
            positions = await self.order_manager.get_open_positions()
            
            # Calculate total portfolio value and positions
            total_value = 0
            position_values = {}
            
            for position in positions:
                symbol = position["symbol"]
                size = float(position["contracts"])
                price = float(position["entryPrice"])
                value = abs(size * price)
                
                position_values[symbol] = {
                    "size": size,
                    "entry_price": price,
                    "current_value": value,
                    "unrealized_pnl": float(position["unrealizedPnl"]),
                    "liquidation_price": float(position.get("liquidationPrice", 0))
                }
                total_value += value
            
            # Calculate current allocations
            current_allocations = {
                symbol: details["current_value"] / total_value
                for symbol, details in position_values.items()
            }
            
            return {
                "total_value": total_value,
                "positions": position_values,
                "current_allocations": current_allocations,
                "target_allocations": self.target_allocations
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {str(e)}")
            raise

    async def set_target_allocations(
        self,
        allocations: Dict[str, float]
    ) -> Dict:
        """Set target allocations for portfolio assets."""
        try:
            # Validate allocations sum to 1
            total_allocation = sum(allocations.values())
            if not 0.99 <= total_allocation <= 1.01:
                raise ValueError("Target allocations must sum to 1.0")
            
            # Validate individual allocations
            for symbol, allocation in allocations.items():
                if allocation < self.min_position_size:
                    raise ValueError(
                        f"Allocation for {symbol} is below minimum {self.min_position_size}"
                    )
                if allocation > self.max_position_size:
                    raise ValueError(
                        f"Allocation for {symbol} exceeds maximum {self.max_position_size}"
                    )
            
            self.target_allocations = allocations
            
            # Check if rebalance is needed
            rebalance_needed = await self._check_rebalance_needed()
            
            return {
                "status": "success",
                "target_allocations": self.target_allocations,
                "rebalance_needed": rebalance_needed
            }
            
        except Exception as e:
            self.logger.error(f"Error setting target allocations: {str(e)}")
            raise

    async def _check_rebalance_needed(self) -> bool:
        """Check if portfolio rebalancing is needed."""
        try:
            if not self.target_allocations:
                return False
                
            summary = await self.get_portfolio_summary()
            current_allocations = summary["current_allocations"]
            
            for symbol, target in self.target_allocations.items():
                current = current_allocations.get(symbol, 0)
                if abs(current - target) > self.rebalance_threshold:
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking rebalance need: {str(e)}")
            raise

    async def rebalance_portfolio(self) -> List[Dict]:
        """Rebalance portfolio to match target allocations."""
        try:
            if not self.target_allocations:
                raise ValueError("No target allocations set")
                
            summary = await self.get_portfolio_summary()
            total_value = summary["total_value"]
            current_positions = summary["positions"]
            
            orders = []
            
            # Calculate required position adjustments
            for symbol, target_allocation in self.target_allocations.items():
                target_value = total_value * target_allocation
                current_value = current_positions.get(symbol, {}).get("current_value", 0)
                
                if abs(current_value - target_value) > (target_value * self.rebalance_threshold):
                    # Calculate required position adjustment
                    current_size = current_positions.get(symbol, {}).get("size", 0)
                    current_price = current_positions.get(symbol, {}).get("entry_price", 0)
                    
                    if current_price == 0:
                        # Fetch current market price for new positions
                        ticker = await self.order_manager.exchange.fetch_ticker(symbol)
                        current_price = ticker["last"]
                    
                    target_size = target_value / current_price
                    size_diff = target_size - current_size
                    
                    if abs(size_diff) > 0:
                        # Create rebalancing order
                        order = await self.order_manager.create_order(
                            symbol=symbol,
                            order_type=OrderType.MARKET,
                            side=OrderSide.BUY if size_diff > 0 else OrderSide.SELL,
                            amount=abs(size_diff)
                        )
                        
                        orders.append({
                            "symbol": symbol,
                            "action": "buy" if size_diff > 0 else "sell",
                            "size": abs(size_diff),
                            "order": order
                        })
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Error rebalancing portfolio: {str(e)}")
            raise

    async def calculate_portfolio_metrics(
        self,
        timeframe: str = "1d",
        lookback_periods: int = 30
    ) -> Dict:
        """Calculate portfolio performance metrics."""
        try:
            summary = await self.get_portfolio_summary()
            positions = summary["positions"]
            
            # Fetch historical data for all positions
            historical_data = {}
            returns_data = {}
            
            for symbol in positions.keys():
                ohlcv = await self.order_manager.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    limit=lookback_periods
                )
                
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['returns'] = df['close'].pct_change()
                
                historical_data[symbol] = df
                returns_data[symbol] = df['returns']
            
            # Calculate portfolio metrics
            if returns_data:
                # Create returns matrix
                returns_matrix = pd.DataFrame(returns_data)
                
                # Calculate portfolio returns using current allocations
                portfolio_returns = returns_matrix.mul(
                    pd.Series(summary["current_allocations"])
                ).sum(axis=1)
                
                # Calculate metrics
                total_return = (1 + portfolio_returns).prod() - 1
                volatility = portfolio_returns.std() * np.sqrt(252)  # Annualized
                sharpe_ratio = (portfolio_returns.mean() - self.risk_free_rate/252) / portfolio_returns.std() * np.sqrt(252)
                
                # Calculate maximum drawdown
                cum_returns = (1 + portfolio_returns).cumprod()
                rolling_max = cum_returns.expanding().max()
                drawdowns = cum_returns / rolling_max - 1
                max_drawdown = drawdowns.min()
                
                # Calculate correlation matrix
                correlation_matrix = returns_matrix.corr().to_dict()
                
                metrics = {
                    "total_return": total_return,
                    "volatility": volatility,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "correlation_matrix": correlation_matrix,
                    "current_drawdown": drawdowns.iloc[-1],
                    "risk_contribution": self._calculate_risk_contribution(returns_matrix, summary["current_allocations"])
                }
            else:
                metrics = {
                    "total_return": 0,
                    "volatility": 0,
                    "sharpe_ratio": 0,
                    "max_drawdown": 0,
                    "correlation_matrix": {},
                    "current_drawdown": 0,
                    "risk_contribution": {}
                }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {str(e)}")
            raise

    def _calculate_risk_contribution(
        self,
        returns_matrix: pd.DataFrame,
        allocations: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate risk contribution of each asset."""
        try:
            # Calculate covariance matrix
            cov_matrix = returns_matrix.cov()
            
            # Convert allocations to series
            weights = pd.Series(allocations)
            
            # Calculate portfolio volatility
            portfolio_vol = np.sqrt(weights.dot(cov_matrix).dot(weights))
            
            # Calculate marginal risk contribution
            mrc = cov_matrix.dot(weights) / portfolio_vol
            
            # Calculate component risk contribution
            rc = weights * mrc
            
            return rc.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error calculating risk contribution: {str(e)}")
            return {}
