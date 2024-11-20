import os
import sys
import pytest
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

# Import necessary fixtures
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def test_client():
    """Fixture that creates a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def test_db():
    """Fixture for test database connection"""
    from database.db_config import DatabaseManager
    # Use test database configuration
    db_manager = DatabaseManager(
        mongo_uri="mongodb://localhost:27017",
        database_name="cryptotrader_test"
    )
    return db_manager

@pytest.fixture
def mock_exchange():
    """Fixture for mocked exchange"""
    class MockExchange:
        def fetch_ohlcv(self, symbol, timeframe, since=None, limit=None):
            return []
        
        def create_order(self, symbol, type, side, amount, price=None):
            return {"id": "test_order_id"}
        
        def fetch_order(self, id, symbol=None):
            return {"status": "closed"}
    
    return MockExchange()
