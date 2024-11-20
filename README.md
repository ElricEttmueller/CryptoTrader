# CryptoTrader

A sophisticated cryptocurrency trading platform with ML-powered analysis and real-time market data integration.

## Features

- Real-time market data streaming
- Automated trading strategies
- Machine Learning-based predictions
- Portfolio management and tracking
- Risk management system
- Backtesting capabilities
- Technical analysis indicators
- Web and desktop interfaces

## Project Structure

```
├── backend/               # FastAPI backend server
│   ├── auth/             # Authentication system
│   ├── bots/             # Trading bot implementations
│   ├── database/         # Database interactions
│   ├── models/           # Data models
│   ├── routes/           # API endpoints
│   ├── strategies/       # Trading strategies
│   ├── trading/          # Core trading functionality
│   └── utils/            # Utility functions
├── frontend/             # React/TypeScript frontend
├── docs/                 # Documentation
└── visualizations/       # Trading visualizations
```

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd CryptoTrader
```

2. Install backend dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start the application:
```bash
./start.bat
```

## Development

- Backend runs on FastAPI (default: http://localhost:8000)
- Frontend development server (default: http://localhost:3000)
- API documentation available at http://localhost:8000/docs

## Testing

Run backend tests:
```bash
cd backend
pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
