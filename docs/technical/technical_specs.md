# CryptoTrader Technical Documentation

## Project Architecture

### Directory Structure
```
CryptoTrader/
├── backend/
│   ├── __init__.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── ml_strategy.py (MLTradingStrategy)
│   │   ├── adaptive_strategy.py
│   │   ├── base_strategy.py
│   │   └── ...
│   ├── utils/
│   │   ├── __init__.py
│   │   └── data_loader.py (DataLoader)
│   ├── database/
│   │   └── db_config.py (DatabaseManager)
│   └── trading/
│       ├── order_manager.py
│       ├── portfolio_manager.py
│       └── risk_manager.py
└── frontend/
    └── ml_dashboard.py (Streamlit Dashboard)
```

## Core Dependencies

### Backend Dependencies
- **FastAPI (>=0.68.0)**
  - Primary web framework for API endpoints
  - Handles HTTP requests and WebSocket connections
  - WebSocket server runs on port 8000
  - Used in: backend/main.py

- **CCXT (>=2.0.0)**
  - Cryptocurrency exchange trading library
  - Handles market data fetching and trading operations
  - Async support for real-time operations
  - Used in: backend/utils/data_loader.py, backend/trading/order_manager.py

- **Pandas (>=1.3.0)**
  - Data manipulation and analysis
  - Used across all strategy implementations and data processing
  - Used in: backend/strategies/*, backend/utils/data_loader.py

- **MongoDB Integration**
  - motor (>=3.1.1): Async MongoDB driver
  - pymongo (>=4.3.3): MongoDB client
  - Unique indexes for strategy configurations
  - Used in: backend/database/db_config.py

### Frontend Dependencies
- **Streamlit (>=1.15.0)**
  - Web interface framework
  - Real-time data visualization
  - WebSocket client for live updates
  - Used in: frontend/ml_dashboard.py

- **Plotly (>=5.3.1)**
  - Interactive visualization library
  - Used for creating trading charts and metrics displays
  - Used in: frontend/ml_dashboard.py

### Machine Learning Dependencies
- **scikit-learn (>=0.24.2)**
  - ML model implementation and feature processing
  - Used in: backend/strategies/ml_strategy.py

- **Technical Analysis (ta>=0.7.0)**
  - Technical indicators calculation
  - Used in: backend/strategies/ml_strategy.py, backend/strategies/adaptive_strategy.py

## Real-time Data Flow
```
[Exchange API] 
     ↓
[CCXT Async] → [WebSocket Server :8000]
     ↓              ↓
[Data Processing] → [Frontend WebSocket Client]
     ↓              ↓
[MongoDB] ← → [Streamlit Dashboard]
```

## Database Schema
### Collections and Indexes
1. **trades**
   - Indexes:
     - timestamp (DESC)
     - (symbol, timestamp) (ASC, DESC)
     - user_id (ASC)

2. **historical_data**
   - Indexes:
     - (symbol, timestamp, timeframe) (ASC, DESC, ASC)

3. **portfolio_snapshots**
   - Indexes:
     - (user_id, timestamp) (ASC, DESC)

4. **positions**
   - Indexes:
     - (user_id, symbol) (ASC, ASC) [unique]

5. **strategy_configs**
   - Indexes:
     - (user_id, strategy_name) (ASC, ASC) [unique]

## Component Interactions

### Data Flow
1. **Market Data Pipeline**
   ```
   CCXT Exchange API → DataLoader → Strategy Classes → ML Dashboard
   ```
   - DataLoader fetches raw market data
   - Strategy classes process and analyze data
   - Dashboard visualizes results

2. **Trading Pipeline**
   ```
   Strategy Signal → OrderManager → RiskManager → Exchange
   ```
   - Strategies generate trading signals
   - OrderManager validates and formats orders
   - RiskManager applies risk controls
   - Final orders sent to exchange

### Class Dependencies

1. **MLTradingStrategy**
   - Inherits from: BaseStrategy
   - Dependencies:
     - DataLoader (market data)
     - scikit-learn (ML models)
     - ta (technical indicators)

2. **DataLoader**
   - Dependencies:
     - CCXT (exchange interface)
     - Pandas (data processing)

3. **OrderManager**
   - Dependencies:
     - CCXT (trade execution)
     - RiskManager (risk validation)
     - DatabaseManager (order logging)

## Import Structure

### Frontend Imports
```python
# ml_dashboard.py
import streamlit as st
from strategies.ml_strategy import MLTradingStrategy
from strategies.adaptive_strategy import AdaptiveStrategy
from utils.data_loader import DataLoader
```

### Backend Imports
```python
# strategies/ml_strategy.py
from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
```

## Configuration Management

### Environment Variables (.env)
- Exchange API credentials
- Database connection strings
- Risk management parameters
- Model hyperparameters

### Runtime Configuration
- Trading pairs
- Strategy parameters
- Risk limits
- Database settings

## Testing Structure

### Required Testing Dependencies
- pytest (>=6.2.5)
- pytest-asyncio (>=0.15.1)

### Test Files
- test_adaptive_strategy.py
- test_backtest.py
- test_db_connection.py
- test_db_manager.py
- test_strategy.py

## Deployment Notes

### Python Path Configuration
- Backend directory must be in PYTHONPATH
- Relative imports used throughout project
- Path configuration handled in frontend scripts

### Database Setup
- MongoDB required for production
- Requires proper authentication setup
- Indexes for performance optimization

## Error Handling

### Critical Points
1. Exchange API connections
2. Database operations
3. Strategy execution
4. Order placement

### Logging
- Structured logging throughout
- Separate logs for:
  - Trading operations
  - Strategy execution
  - System errors

## Future Considerations

### Planned Features
1. Real-time WebSocket data feeds
2. Additional ML models integration
3. Enhanced backtesting capabilities
4. Portfolio optimization algorithms

### Scalability Points
1. Database sharding
2. Async operation optimization
3. Load balancing for multiple instances
4. Caching layer implementation
