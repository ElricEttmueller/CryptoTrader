import pytest
from fastapi.testclient import TestClient
from main import app
from models.bot import BotConfig
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Fixture for authentication headers"""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def sample_bot_config():
    """Fixture for sample bot configuration"""
    return {
        "name": "Test Bot",
        "strategy": "MeanReversion",
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "config": {
            "window_size": 20,
            "std_dev_threshold": 2.0,
            "position_size": 0.1
        }
    }

def test_create_bot(auth_headers, sample_bot_config):
    """Test bot creation endpoint"""
    with patch('routes.bot.BotManager.create_bot') as mock_create:
        mock_create.return_value = "bot_123"
        response = client.post(
            "/api/bots/create",
            json=sample_bot_config,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "bot_id" in response.json()

def test_list_bots(auth_headers):
    """Test bot listing endpoint"""
    with patch('routes.bot.BotManager.list_bots') as mock_list:
        mock_list.return_value = [
            {
                "id": "bot_123",
                "name": "Test Bot",
                "strategy": "MeanReversion",
                "status": "running"
            }
        ]
        response = client.get("/api/bots/list", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json()["bots"], list)

def test_start_bot(auth_headers):
    """Test bot start endpoint"""
    with patch('routes.bot.BotManager.start_bot') as mock_start:
        mock_start.return_value = True
        response = client.post(
            "/api/bots/bot_123/start",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "started"

def test_stop_bot(auth_headers):
    """Test bot stop endpoint"""
    with patch('routes.bot.BotManager.stop_bot') as mock_stop:
        mock_stop.return_value = True
        response = client.post(
            "/api/bots/bot_123/stop",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"

def test_get_bot_status(auth_headers):
    """Test bot status endpoint"""
    with patch('routes.bot.BotManager.get_bot_status') as mock_status:
        mock_status.return_value = {
            "status": "running",
            "current_position": 0.1,
            "unrealized_pnl": 100.50
        }
        response = client.get(
            "/api/bots/bot_123/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "status" in response.json()

def test_get_bot_performance(auth_headers):
    """Test bot performance endpoint"""
    with patch('routes.bot.BotManager.get_bot_performance') as mock_perf:
        mock_perf.return_value = {
            "total_return": 15.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": -5.0
        }
        response = client.get(
            "/api/bots/bot_123/performance",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "total_return" in response.json()

def test_invalid_bot_id(auth_headers):
    """Test handling of invalid bot ID"""
    response = client.get(
        "/api/bots/invalid_id/status",
        headers=auth_headers
    )
    assert response.status_code == 404

def test_unauthorized_access():
    """Test unauthorized access"""
    response = client.get("/api/bots/list")
    assert response.status_code == 401
