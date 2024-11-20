from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import asyncio
import logging
from dataclasses import dataclass

@dataclass
class BotConfig:
    name: str
    pair: str
    timeframe: str
    strategy: Dict[str, Any]
    signals: List[Dict[str, Any]]
    risk_params: Dict[str, Any]

class BotState:
    CREATED = "created"
    CONFIGURED = "configured"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class BotBase(ABC):
    def __init__(self, config: BotConfig):
        self.config = config
        self.state = BotState.CREATED
        self.logger = logging.getLogger(f"bot.{config.name}")
        self.last_run: datetime = None
        self.strategy = None
        self.signals = []
        self._stop_event = asyncio.Event()
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize bot components and validate configuration"""
        pass
        
    @abstractmethod
    async def execute(self) -> None:
        """Execute one iteration of the bot's trading logic"""
        pass
        
    async def start(self) -> None:
        """Start the bot's main loop"""
        try:
            await self.initialize()
            self.state = BotState.RUNNING
            self.logger.info(f"Bot {self.config.name} started")
            
            while not self._stop_event.is_set():
                try:
                    await self.execute()
                    self.last_run = datetime.utcnow()
                    await asyncio.sleep(1)  # Prevent tight loop
                except Exception as e:
                    self.logger.error(f"Error in bot execution: {str(e)}")
                    self.state = BotState.ERROR
                    raise
                    
        except Exception as e:
            self.logger.error(f"Fatal error in bot: {str(e)}")
            self.state = BotState.ERROR
            raise
            
    async def stop(self) -> None:
        """Stop the bot gracefully"""
        self._stop_event.set()
        self.state = BotState.STOPPED
        self.logger.info(f"Bot {self.config.name} stopped")
        
    async def pause(self) -> None:
        """Pause the bot temporarily"""
        if self.state == BotState.RUNNING:
            self.state = BotState.PAUSED
            self.logger.info(f"Bot {self.config.name} paused")
            
    async def resume(self) -> None:
        """Resume a paused bot"""
        if self.state == BotState.PAUSED:
            self.state = BotState.RUNNING
            self.logger.info(f"Bot {self.config.name} resumed")
            
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate bot configuration"""
        pass
        
    @abstractmethod
    async def load_strategy(self) -> Any:
        """Load and initialize the trading strategy"""
        pass
        
    @abstractmethod
    async def load_signals(self) -> List[Any]:
        """Load and initialize trading signals"""
        pass
        
    async def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        return {
            "name": self.config.name,
            "state": self.state,
            "pair": self.config.pair,
            "last_run": self.last_run,
            "strategy": self.strategy.__class__.__name__ if self.strategy else None,
            "signals": [s.__class__.__name__ for s in self.signals],
        }
        
    async def handle_alerts(self) -> None:
        """Handle any alerts or notifications"""
        pass
