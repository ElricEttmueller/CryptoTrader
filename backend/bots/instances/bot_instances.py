from typing import Dict, List, Optional, Type
import logging
import asyncio
from datetime import datetime

from ..base.bot_base import BotBase, BotConfig, BotState
from ..strategies import AVAILABLE_STRATEGIES
from ..signals import AVAILABLE_SIGNALS

class BotManager:
    def __init__(self):
        """Initialize bot manager"""
        self.bots: Dict[str, BotBase] = {}
        self.logger = logging.getLogger(__name__)
        
    async def create_bot(self, config: BotConfig) -> BotBase:
        """Create a new bot instance"""
        try:
            # Check if bot with same name exists
            if config.name in self.bots:
                raise ValueError(f"Bot with name {config.name} already exists")
                
            # Validate strategy
            strategy_class = AVAILABLE_STRATEGIES.get(config.strategy["name"])
            if not strategy_class:
                raise ValueError(f"Strategy {config.strategy['name']} not found")
                
            # Validate signals
            for signal_config in config.signals:
                signal_class = AVAILABLE_SIGNALS.get(signal_config["name"])
                if not signal_class:
                    raise ValueError(f"Signal {signal_config['name']} not found")
                    
            # Create bot instance with validated config
            bot = BotBase(config)
            self.bots[config.name] = bot
            
            self.logger.info(f"Created bot {config.name}")
            return bot
            
        except Exception as e:
            self.logger.error(f"Error creating bot: {str(e)}")
            raise
            
    async def get_bot(self, bot_id: str) -> Optional[BotBase]:
        """Get bot by ID"""
        return self.bots.get(bot_id)
        
    async def list_bots(self) -> List[BotBase]:
        """List all bots"""
        return list(self.bots.values())
        
    async def delete_bot(self, bot_id: str) -> bool:
        """Delete a bot"""
        try:
            if bot_id not in self.bots:
                return False
                
            bot = self.bots[bot_id]
            if bot.state == BotState.RUNNING:
                await bot.stop()
                
            del self.bots[bot_id]
            self.logger.info(f"Deleted bot {bot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting bot: {str(e)}")
            return False
            
    async def start_all_bots(self) -> Dict[str, str]:
        """Start all bots"""
        results = {}
        for bot_id, bot in self.bots.items():
            try:
                await bot.start()
                results[bot_id] = "started"
            except Exception as e:
                self.logger.error(f"Error starting bot {bot_id}: {str(e)}")
                results[bot_id] = f"error: {str(e)}"
        return results
        
    async def stop_all_bots(self) -> Dict[str, str]:
        """Stop all bots"""
        results = {}
        for bot_id, bot in self.bots.items():
            try:
                await bot.stop()
                results[bot_id] = "stopped"
            except Exception as e:
                self.logger.error(f"Error stopping bot {bot_id}: {str(e)}")
                results[bot_id] = f"error: {str(e)}"
        return results
        
    async def get_active_bots(self) -> List[BotBase]:
        """Get list of running bots"""
        return [bot for bot in self.bots.values() if bot.state == BotState.RUNNING]
        
    async def get_bot_status(self, bot_id: str) -> Optional[Dict]:
        """Get detailed bot status"""
        bot = await self.get_bot(bot_id)
        if not bot:
            return None
        return await bot.get_status()
        
    async def update_bot_config(self, bot_id: str, new_config: Dict) -> bool:
        """Update bot configuration"""
        try:
            bot = await self.get_bot(bot_id)
            if not bot:
                return False
                
            # Stop bot if running
            was_running = bot.state == BotState.RUNNING
            if was_running:
                await bot.stop()
                
            # Update config
            bot.config = BotConfig(**new_config)
            await bot.initialize()
            
            # Restart if it was running
            if was_running:
                await bot.start()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating bot config: {str(e)}")
            return False
            
    async def cleanup(self):
        """Cleanup all bots"""
        await self.stop_all_bots()
        self.bots.clear()
