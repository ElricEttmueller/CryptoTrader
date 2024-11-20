from typing import Dict, Type
from ..base.strategy_base import StrategyBase

# Import your strategy implementations here
from .mean_reversion import MeanReversionStrategy
from .trend_following import TrendFollowingStrategy

# Register available strategies
AVAILABLE_STRATEGIES: Dict[str, Type[StrategyBase]] = {
    "MeanReversion": MeanReversionStrategy,
    "TrendFollowing": TrendFollowingStrategy,
}

__all__ = [
    "AVAILABLE_STRATEGIES",
    "MeanReversionStrategy",
    "TrendFollowingStrategy",
]
