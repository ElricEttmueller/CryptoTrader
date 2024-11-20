# Getting Started with CryptoTrader

## Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB 4.4+
- TimescaleDB (PostgreSQL 12+)
- Docker (optional)

## Installation

### Backend Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/cryptotrader.git
cd cryptotrader
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Frontend Setup
1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

### Backend Configuration
The `.env` file contains important configuration settings:

```env
# Server Configuration
API_HOST=localhost
API_PORT=8000
DEBUG=True

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/cryptotrader
TIMESCALEDB_URI=postgresql://user:password@localhost:5432/cryptotrader

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Exchange API Keys
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-api-secret
```

### Frontend Configuration
Configure the frontend in `.env`:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

## Quick Start Guide

### 1. Start the Backend
```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### 2. Start the Frontend
```bash
cd frontend
npm start
```

The web interface will be available at `http://localhost:3000`

### 3. Create Your First Bot

1. Log in to the web interface
2. Navigate to "Bot Management"
3. Click "Create New Bot"
4. Choose a strategy (e.g., "Mean Reversion")
5. Configure the strategy parameters
6. Start the bot

### 4. Monitor Performance

1. Navigate to "Dashboard"
2. View real-time performance metrics
3. Check trading history
4. Monitor portfolio value

## Docker Deployment

### Using Docker Compose
1. Build and start services:
```bash
docker-compose up -d
```

2. Stop services:
```bash
docker-compose down
```

## Next Steps
- Read the [Strategy Development Guide](./strategies/development.md) to create custom strategies
- Check the [API Documentation](./api/README.md) for integrating with other systems
- Review [Security Best Practices](./security.md) for production deployment

## Troubleshooting
If you encounter issues:

1. Check the logs:
```bash
tail -f logs/cryptotrader.log
```

2. Verify database connections:
```bash
python scripts/test_db_connection.py
```

3. Ensure all required services are running:
```bash
python scripts/check_services.py
```

For more detailed troubleshooting, refer to the [Troubleshooting Guide](./troubleshooting.md).
