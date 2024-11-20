from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class MarketData:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    pair: str
    timeframe: str
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class TradeDecision:
    action: str  # 'buy', 'sell', 'hold'
    pair: str
    price: Optional[float]
    amount: Optional[float]
    reason: str
    confidence: float
    timestamp: datetime
    params: Optional[Dict[str, Any]] = None

class StrategyBase(ABC):
    def __init__(self, params: Dict[str, Any]):
        """Initialize strategy with parameters"""
        self.params = params
        self.name = self.__class__.__name__
        self._validate_params()
        
    @abstractmethod
    def _validate_params(self) -> None:
        """Validate strategy parameters"""
        pass
        
    @abstractmethod
    async def analyze(self, data: MarketData) -> TradeDecision:
        """Analyze market data and make trading decision"""
        pass
        
    @abstractmethod
    async def calculate_position_size(self, 
                                    capital: float, 
                                    price: float, 
                                    risk_per_trade: float) -> float:
        """Calculate position size based on available capital and risk parameters"""
        pass
        
    async def preprocess_data(self, data: MarketData) -> MarketData:
        """Preprocess market data before analysis"""
        return data
        
    async def validate_decision(self, decision: TradeDecision) -> bool:
        """Validate trading decision before execution"""
        if not decision.action in ['buy', 'sell', 'hold']:
            return False
        if decision.action != 'hold' and (not decision.price or not decision.amount):
            return False
        return True
        
    @abstractmethod
    async def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators used by the strategy"""
        pass
        
    @abstractmethod
    async def get_stop_loss(self, 
                           entry_price: float, 
                           position_type: str) -> float:
        """Calculate stop loss price for a position"""
        pass
        
    @abstractmethod
    async def get_take_profit(self, 
                             entry_price: float, 
                             position_type: str) -> float:
        """Calculate take profit price for a position"""
        pass
        
    async def update_parameters(self, new_params: Dict[str, Any]) -> None:
        """Update strategy parameters"""
        self.params.update(new_params)
        self._validate_params()
        
    @abstractmethod
    async def get_risk_reward_ratio(self, 
                                   entry_price: float,
                                   stop_loss: float,
                                   take_profit: float) -> float:
        """Calculate risk/reward ratio for a potential trade"""
        pass
        
    async def should_update_position(self, 
                                   current_position: Dict[str, Any],
                                   current_price: float) -> bool:
        """Determine if current position should be updated"""
        return False  # Default implementation
        
    @property
    def description(self) -> str:
        """Get strategy description"""
        return f"{self.name} Strategy"
        
    @property
    def required_indicators(self) -> list:
        """List required technical indicators"""
        return []
        
    @property
    def timeframe_restrictions(self) -> list:
        """List supported timeframes"""
        return []  # Empty means all timeframes supported
