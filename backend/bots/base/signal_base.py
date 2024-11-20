from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class SignalResult:
    name: str
    value: float
    signal_type: str  # 'buy', 'sell', 'neutral'
    strength: float  # 0.0 to 1.0
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class SignalBase(ABC):
    def __init__(self, params: Dict[str, Any]):
        """Initialize signal with parameters"""
        self.params = params
        self.name = self.__class__.__name__
        self._validate_params()
        
    @abstractmethod
    def _validate_params(self) -> None:
        """Validate signal parameters"""
        pass
        
    @abstractmethod
    async def generate(self, data: pd.DataFrame) -> SignalResult:
        """Generate trading signal from market data"""
        pass
        
    @abstractmethod
    async def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate signal value from market data"""
        pass
        
    async def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess market data before signal generation"""
        return data
        
    @abstractmethod
    async def get_threshold(self, signal_type: str) -> float:
        """Get threshold value for signal type"""
        pass
        
    async def combine_signals(self, signals: list) -> SignalResult:
        """Combine multiple signal results into one"""
        if not signals:
            return None
            
        # Default implementation: average signal values and strengths
        total_value = sum(s.value for s in signals)
        total_strength = sum(s.strength for s in signals)
        avg_value = total_value / len(signals)
        avg_strength = total_strength / len(signals)
        
        # Determine overall signal type based on majority
        signal_types = [s.signal_type for s in signals]
        overall_type = max(set(signal_types), key=signal_types.count)
        
        return SignalResult(
            name=f"Combined_{self.name}",
            value=avg_value,
            signal_type=overall_type,
            strength=avg_strength,
            timestamp=datetime.utcnow(),
            metadata={"component_signals": [s.name for s in signals]}
        )
        
    @abstractmethod
    async def validate_signal(self, signal: SignalResult) -> bool:
        """Validate generated signal"""
        pass
        
    async def update_parameters(self, new_params: Dict[str, Any]) -> None:
        """Update signal parameters"""
        self.params.update(new_params)
        self._validate_params()
        
    @property
    def description(self) -> str:
        """Get signal description"""
        return f"{self.name} Signal"
        
    @property
    def required_data(self) -> list:
        """List required data fields"""
        return ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
    @property
    def signal_types(self) -> list:
        """List supported signal types"""
        return ['buy', 'sell', 'neutral']
        
    @abstractmethod
    async def get_confidence_level(self, signal: SignalResult) -> float:
        """Calculate confidence level of the signal"""
        pass
        
    @abstractmethod
    async def should_update(self, 
                           current_signal: SignalResult,
                           new_data: pd.DataFrame) -> bool:
        """Determine if signal should be updated based on new data"""
        pass
