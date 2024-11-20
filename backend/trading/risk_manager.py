from typing import Dict, Optional, List
import logging
from decimal import Decimal
from enum import Enum
from datetime import datetime
import pandas as pd
import numpy as np
from .order_manager import OrderManager, OrderType, OrderSide

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskManager:
    def __init__(
        self,
        order_manager: OrderManager,
        max_position_size: float = 0.1,  # 10% of portfolio
        max_portfolio_risk: float = 0.02,  # 2% risk per trade
        max_drawdown: float = 0.15,  # 15% maximum drawdown
        volatility_lookback: int = 20,  # periods for volatility calculation
        risk_free_rate: float = 0.02,  # 2% risk-free rate
    ):
        self.order_manager = order_manager
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.max_drawdown = max_drawdown
        self.volatility_lookback = volatility_lookback
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
        self.position_stops: Dict[str, Dict] = {}

    async def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        portfolio_value: float,
        risk_level: RiskLevel = RiskLevel.MEDIUM
    ) -> Dict:
        """Calculate the appropriate position size based on risk parameters."""
        try:
            # Calculate risk per trade based on risk level
            risk_multiplier = {
                RiskLevel.LOW: 0.5,
                RiskLevel.MEDIUM: 1.0,
                RiskLevel.HIGH: 1.5
            }[risk_level]
            
            risk_amount = portfolio_value * self.max_portfolio_risk * risk_multiplier
            
            # Calculate position size based on stop loss distance
            stop_distance_percent = abs(entry_price - stop_loss) / entry_price
            position_size = risk_amount / stop_distance_percent
            
            # Ensure position size doesn't exceed maximum allowed
            max_allowed_position = portfolio_value * self.max_position_size
            position_size = min(position_size, max_allowed_position)
            
            return {
                "position_size": position_size,
                "risk_amount": risk_amount,
                "max_loss": risk_amount,
                "stop_distance_percent": stop_distance_percent * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            raise

    async def set_stop_loss(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        stop_price: float,
        is_trailing: bool = False,
        callback_rate: Optional[float] = None
    ) -> Dict:
        """Set a stop-loss order for a position."""
        try:
            params = {}
            if is_trailing and callback_rate:
                params["trailing_stop"] = True
                params["callback_rate"] = callback_rate
                
            order = await self.order_manager.create_order(
                symbol=symbol,
                order_type=OrderType.STOP_LOSS,
                side=OrderSide.SELL,
                amount=position_size,
                price=stop_price,
                params=params
            )
            
            self.position_stops[symbol] = {
                "stop_order_id": order["id"],
                "stop_price": stop_price,
                "is_trailing": is_trailing,
                "callback_rate": callback_rate
            }
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error setting stop loss: {str(e)}")
            raise

    async def set_take_profit(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        profit_targets: List[Dict[str, float]]  # [{"price": float, "size": float}]
    ) -> List[Dict]:
        """Set multiple take-profit orders at different price levels."""
        try:
            orders = []
            remaining_size = position_size
            
            for target in profit_targets:
                if remaining_size <= 0:
                    break
                    
                target_size = min(position_size * target["size"], remaining_size)
                
                order = await self.order_manager.create_order(
                    symbol=symbol,
                    order_type=OrderType.TAKE_PROFIT,
                    side=OrderSide.SELL,
                    amount=target_size,
                    price=target["price"]
                )
                
                orders.append(order)
                remaining_size -= target_size
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Error setting take profit: {str(e)}")
            raise

    def calculate_risk_metrics(
        self,
        prices: pd.Series,
        positions: Dict[str, Dict]
    ) -> Dict:
        """Calculate various risk metrics for the portfolio."""
        try:
            # Calculate returns
            returns = prices.pct_change().dropna()
            
            # Calculate volatility
            volatility = returns.rolling(window=self.volatility_lookback).std() * np.sqrt(252)
            
            # Calculate Sharpe ratio
            excess_returns = returns - self.risk_free_rate / 252
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()
            
            # Calculate maximum drawdown
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = cumulative_returns / rolling_max - 1
            max_drawdown = drawdowns.min()
            
            # Calculate portfolio exposure
            total_exposure = sum(
                abs(float(pos["amount"]) * float(pos["entry_price"]))
                for pos in positions.values()
            )
            
            return {
                "volatility": volatility.iloc[-1],
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "total_exposure": total_exposure,
                "current_drawdown": drawdowns.iloc[-1],
                "risk_level": self._assess_risk_level(volatility.iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {str(e)}")
            raise

    def _assess_risk_level(self, volatility: float) -> RiskLevel:
        """Assess the current risk level based on volatility."""
        if volatility < 0.2:  # Less than 20% annualized volatility
            return RiskLevel.LOW
        elif volatility < 0.4:  # Less than 40% annualized volatility
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    async def check_portfolio_limits(self, portfolio_value: float) -> Dict:
        """Check if current positions are within portfolio limits."""
        try:
            positions = await self.order_manager.get_open_positions()
            
            total_exposure = sum(
                abs(float(pos["contracts"]) * float(pos["entryPrice"]))
                for pos in positions
            )
            
            exposure_ratio = total_exposure / portfolio_value
            
            return {
                "within_limits": exposure_ratio <= 1,
                "current_exposure": exposure_ratio,
                "max_allowed_exposure": 1,
                "available_margin": portfolio_value * (1 - exposure_ratio)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking portfolio limits: {str(e)}")
            raise

    async def adjust_position_sizes(
        self,
        symbol: str,
        volatility_change: float
    ) -> Optional[Dict]:
        """Adjust position sizes based on changing market conditions."""
        try:
            position = await self.order_manager.update_position(symbol)
            if not position:
                return None
                
            current_size = float(position["amount"])
            current_exposure = abs(current_size * float(position["entry_price"]))
            
            # Adjust size based on volatility change
            if volatility_change > 0.5:  # Volatility increased by 50%
                # Reduce position size
                new_size = current_size * 0.7  # Reduce by 30%
                
                if new_size != current_size:
                    # Create order to adjust position
                    adjustment_size = abs(new_size - current_size)
                    side = OrderSide.SELL if new_size < current_size else OrderSide.BUY
                    
                    order = await self.order_manager.create_order(
                        symbol=symbol,
                        order_type=OrderType.MARKET,
                        side=side,
                        amount=adjustment_size
                    )
                    
                    return {
                        "action": "reduce" if new_size < current_size else "increase",
                        "old_size": current_size,
                        "new_size": new_size,
                        "adjustment_order": order
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error adjusting position sizes: {str(e)}")
            raise
