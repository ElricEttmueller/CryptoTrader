from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from datetime import datetime
import json
import subprocess
import sys
from typing import Dict, Any

router = APIRouter()

class MLConfig(BaseModel):
    feature_window: int
    prediction_window: int
    train_split: float
    learning_rate: float
    batch_size: int
    epochs: int

class BacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    initial_balance: float
    strategy: str
    timeframe: str
    ml_config: MLConfig

def get_latest_backtest_dir():
    visualizations_dir = "visualizations"
    if not os.path.exists(visualizations_dir):
        raise HTTPException(status_code=404, detail="No backtest results found")
    
    backtest_dirs = [d for d in os.listdir(visualizations_dir) if d.startswith("backtest_")]
    if not backtest_dirs:
        raise HTTPException(status_code=404, detail="No backtest results found")
    
    latest_dir = max(backtest_dirs, key=lambda x: os.path.getctime(os.path.join(visualizations_dir, x)))
    return os.path.join(visualizations_dir, latest_dir)

@router.get("/trading/metrics")
async def get_trading_metrics():
    try:
        latest_dir = get_latest_backtest_dir()
        with open(os.path.join(latest_dir, "summary.txt"), "r") as f:
            lines = f.readlines()
        
        metrics = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                if "$" in value:
                    value = float(value.replace("$", "").replace(",", ""))
                elif "%" in value:
                    value = float(value.replace("%", "")) / 100
                else:
                    try:
                        value = float(value.replace(",", ""))
                    except ValueError:
                        continue
                metrics[key] = value
        
        return {
            "total_trades": metrics.get("number_of_trades", 0),
            "win_rate": metrics.get("win_rate", 0),
            "total_pnl": metrics.get("total_pnl", 0),
            "avg_win": metrics.get("average_winning_trade", 0),
            "avg_loss": metrics.get("average_losing_trade", 0),
            "largest_win": metrics.get("largest_winning_trade", 0),
            "largest_loss": metrics.get("largest_losing_trade", 0),
            "final_value": metrics.get("final_portfolio_value", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading/viz/{viz_type}", response_class=HTMLResponse)
async def get_visualization(viz_type: str):
    try:
        latest_dir = get_latest_backtest_dir()
        viz_files = {
            "performance": "trading_performance.html",
            "pnl": "pnl_distribution.html",
            "signals": "trading_signals.html",
            "ml": "ml_metrics.html"
        }
        
        if viz_type not in viz_files:
            raise HTTPException(status_code=404, detail="Visualization type not found")
        
        viz_file = os.path.join(latest_dir, viz_files[viz_type])
        if not os.path.exists(viz_file):
            raise HTTPException(status_code=404, detail="Visualization file not found")
        
        with open(viz_file, "r") as f:
            content = f.read()
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trading/backtest")
async def run_backtest(request: BacktestRequest):
    try:
        # Save ML config to a temporary file
        config_path = "temp_config.json"
        with open(config_path, "w") as f:
            json.dump({
                "feature_window": request.ml_config.feature_window,
                "prediction_window": request.ml_config.prediction_window,
                "train_split": request.ml_config.train_split,
                "learning_rate": request.ml_config.learning_rate,
                "batch_size": request.ml_config.batch_size,
                "epochs": request.ml_config.epochs
            }, f)

        # Run the backtest script with the provided configuration
        cmd = [
            sys.executable,
            "run_backtest_with_viz.py",
            "--symbol", request.symbol,
            "--start_date", request.start_date,
            "--end_date", request.end_date,
            "--initial_balance", str(request.initial_balance),
            "--timeframe", request.timeframe,
            "--config", config_path
        ]

        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Backtest failed: {process.stderr}")

        # Clean up the temporary config file
        os.remove(config_path)

        # Get the latest backtest results
        latest_dir = get_latest_backtest_dir()
        with open(os.path.join(latest_dir, "summary.txt"), "r") as f:
            lines = f.readlines()
        
        metrics = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                if "$" in value:
                    value = float(value.replace("$", "").replace(",", ""))
                elif "%" in value:
                    value = float(value.replace("%", "")) / 100
                else:
                    try:
                        value = float(value.replace(",", ""))
                    except ValueError:
                        continue
                metrics[key] = value

        return {
            "status": "success",
            "metrics": {
                "total_trades": metrics.get("number_of_trades", 0),
                "win_rate": metrics.get("win_rate", 0),
                "total_pnl": metrics.get("total_pnl", 0),
                "avg_win": metrics.get("average_winning_trade", 0),
                "avg_loss": metrics.get("average_losing_trade", 0),
                "largest_win": metrics.get("largest_winning_trade", 0),
                "largest_loss": metrics.get("largest_losing_trade", 0),
                "final_value": metrics.get("final_portfolio_value", 0)
            },
            "log": process.stdout
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
