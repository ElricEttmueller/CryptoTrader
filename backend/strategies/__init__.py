from typing import Dict, Type
from .base_strategy import BaseStrategy
from .mean_reversion import MeanReversionStrategy
from .trend_following import TrendFollowingStrategy
from .ma_strategy import MovingAverageStrategy
from .adaptive_strategy import AdaptiveStrategy
from .ml_strategy import MLTradingStrategy
from .rl_strategy import RLTradingStrategy

# Register available strategies
AVAILABLE_STRATEGIES: Dict[str, Type[BaseStrategy]] = {
    'mean_reversion': MeanReversionStrategy,
    'trend_following': TrendFollowingStrategy,
    'moving_average': MovingAverageStrategy,
    'adaptive': AdaptiveStrategy,
    'ml': MLTradingStrategy,
    'rl': RLTradingStrategy
}

__all__ = [
    "AVAILABLE_STRATEGIES",
    "BaseStrategy",
    "MeanReversionStrategy",
    "TrendFollowingStrategy",
    "MovingAverageStrategy",
    "AdaptiveStrategy",
    "MLTradingStrategy",
    "RLTradingStrategy",
]
