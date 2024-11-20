from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
import logging
from datetime import datetime

from ..bots.base.bot_base import BotBase, BotConfig, BotState
from ..bots.instances.bot_instances import BotManager
from .auth import get_api_key

router = APIRouter(prefix="/bots", tags=["bots"])
logger = logging.getLogger(__name__)

# Initialize bot manager
bot_manager = BotManager()

@router.post("/create")
async def create_bot(config: BotConfig, api_key: str = Depends(get_api_key)):
    """Create a new trading bot"""
    try:
        bot = await bot_manager.create_bot(config)
        return {
            "status": "success",
            "bot_id": bot.config.name,
            "state": bot.state
        }
    except Exception as e:
        logger.error(f"Error creating bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_bots(api_key: str = Depends(get_api_key)):
    """List all bots"""
    try:
        bots = await bot_manager.list_bots()
        return {
            "status": "success",
            "bots": [
                {
                    "id": bot.config.name,
                    "state": bot.state,
                    "pair": bot.config.pair,
                    "strategy": bot.config.strategy["name"],
                    "last_run": bot.last_run
                }
                for bot in bots
            ]
        }
    except Exception as e:
        logger.error(f"Error listing bots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bot_id}")
async def get_bot(bot_id: str, api_key: str = Depends(get_api_key)):
    """Get bot details"""
    try:
        bot = await bot_manager.get_bot(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        status = await bot.get_status()
        return {
            "status": "success",
            "bot": status
        }
    except Exception as e:
        logger.error(f"Error getting bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bot_id}/start")
async def start_bot(bot_id: str, api_key: str = Depends(get_api_key)):
    """Start a bot"""
    try:
        bot = await bot_manager.get_bot(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        await bot.start()
        return {
            "status": "success",
            "message": f"Bot {bot_id} started",
            "state": bot.state
        }
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: str, api_key: str = Depends(get_api_key)):
    """Stop a bot"""
    try:
        bot = await bot_manager.get_bot(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        await bot.stop()
        return {
            "status": "success",
            "message": f"Bot {bot_id} stopped",
            "state": bot.state
        }
    except Exception as e:
        logger.error(f"Error stopping bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bot_id}/pause")
async def pause_bot(bot_id: str, api_key: str = Depends(get_api_key)):
    """Pause a bot"""
    try:
        bot = await bot_manager.get_bot(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        await bot.pause()
        return {
            "status": "success",
            "message": f"Bot {bot_id} paused",
            "state": bot.state
        }
    except Exception as e:
        logger.error(f"Error pausing bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{bot_id}/resume")
async def resume_bot(bot_id: str, api_key: str = Depends(get_api_key)):
    """Resume a paused bot"""
    try:
        bot = await bot_manager.get_bot(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        await bot.resume()
        return {
            "status": "success",
            "message": f"Bot {bot_id} resumed",
            "state": bot.state
        }
    except Exception as e:
        logger.error(f"Error resuming bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{bot_id}")
async def delete_bot(bot_id: str, api_key: str = Depends(get_api_key)):
    """Delete a bot"""
    try:
        success = await bot_manager.delete_bot(bot_id)
        if not success:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        return {
            "status": "success",
            "message": f"Bot {bot_id} deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bot_id}/performance")
async def get_bot_performance(
    bot_id: str,
    timeframe: str = "1d",
    limit: int = 30,
    api_key: str = Depends(get_api_key)
):
    """Get bot performance metrics"""
    try:
        bot = await bot_manager.get_bot(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        # This would be implemented in your bot class
        performance = await bot.get_performance_metrics(timeframe, limit)
        return {
            "status": "success",
            "bot_id": bot_id,
            "performance": performance
        }
    except Exception as e:
        logger.error(f"Error getting bot performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
