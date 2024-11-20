# API Documentation

## Overview
CryptoTrader provides a comprehensive REST API and WebSocket interface for managing trading bots, accessing market data, and monitoring performance.

## Authentication
All API endpoints require JWT authentication. To obtain a token:

```bash
POST /api/auth/login
{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer"
}
```

Include the token in all subsequent requests:
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## REST API Endpoints

### Bot Management

#### Create Bot
```bash
POST /api/bots/create
{
    "name": "MyBot",
    "strategy": "MeanReversion",
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "config": {
        "window_size": 20,
        "std_dev_threshold": 2.0,
        "position_size": 0.1
    }
}
```

#### List Bots
```bash
GET /api/bots/list
```

Response:
```json
{
    "bots": [
        {
            "id": "bot_123",
            "name": "MyBot",
            "strategy": "MeanReversion",
            "status": "running",
            "created_at": "2023-01-01T00:00:00Z"
        }
    ]
}
```

#### Start Bot
```bash
POST /api/bots/{bot_id}/start
```

#### Stop Bot
```bash
POST /api/bots/{bot_id}/stop
```

#### Get Bot Status
```bash
GET /api/bots/{bot_id}/status
```

Response:
```json
{
    "id": "bot_123",
    "status": "running",
    "current_position": 0.1,
    "unrealized_pnl": 100.50,
    "total_trades": 50,
    "win_rate": 0.65
}
```

### Market Data

#### Get Historical Data
```bash
GET /api/market/history?symbol=BTC/USDT&interval=1h&limit=1000
```

Response:
```json
{
    "data": [
        {
            "timestamp": "2023-01-01T00:00:00Z",
            "open": 50000.0,
            "high": 51000.0,
            "low": 49000.0,
            "close": 50500.0,
            "volume": 100.5
        }
    ]
}
```

#### Get Current Price
```bash
GET /api/market/price?symbol=BTC/USDT
```

### Performance Metrics

#### Get Bot Performance
```bash
GET /api/bots/{bot_id}/performance
```

Response:
```json
{
    "total_return": 15.5,
    "sharpe_ratio": 1.2,
    "max_drawdown": -5.0,
    "win_rate": 0.65,
    "profit_factor": 1.5,
    "trades": [
        {
            "timestamp": "2023-01-01T00:00:00Z",
            "type": "buy",
            "price": 50000.0,
            "size": 0.1,
            "pnl": 100.5
        }
    ]
}
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Authentication
```javascript
ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'your-jwt-token'
}));
```

### Subscribe to Updates

#### Market Data
```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'market',
    symbol: 'BTC/USDT'
}));
```

#### Bot Updates
```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'bot',
    bot_id: 'bot_123'
}));
```

### Message Types

#### Market Data Update
```json
{
    "type": "market_update",
    "symbol": "BTC/USDT",
    "data": {
        "price": 50000.0,
        "volume": 100.5,
        "timestamp": "2023-01-01T00:00:00Z"
    }
}
```

#### Bot Status Update
```json
{
    "type": "bot_update",
    "bot_id": "bot_123",
    "data": {
        "status": "running",
        "position": 0.1,
        "unrealized_pnl": 100.5,
        "last_signal": "buy"
    }
}
```

#### Trade Execution
```json
{
    "type": "trade",
    "bot_id": "bot_123",
    "data": {
        "type": "buy",
        "symbol": "BTC/USDT",
        "price": 50000.0,
        "size": 0.1,
        "timestamp": "2023-01-01T00:00:00Z"
    }
}
```

## Rate Limits
- Authentication: 5 requests per minute
- Market Data: 60 requests per minute
- Bot Management: 30 requests per minute
- WebSocket: 10 messages per second

## Error Handling

### HTTP Status Codes
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

### Error Response Format
```json
{
    "error": {
        "code": "BOT_NOT_FOUND",
        "message": "Bot with ID bot_123 not found",
        "details": {
            "bot_id": "bot_123"
        }
    }
}
```

## Additional Resources
- [API Reference](./reference.md)
- [Authentication Guide](./authentication.md)
- [WebSocket Guide](./websocket.md)
- [Error Codes](./errors.md)
