# Crypto Trading Platform

A highly customizable cryptocurrency trading platform built with Electron and Python. The platform supports real-time data visualization, trading signals, and backtesting functionalities. The frontend uses React and Electron for a dynamic and modern UI, while the backend uses FastAPI for trading logic, data integration, and API management.

## Features
- **Real-time Data**: Fetch and display live trading data using CCXT.
- **Customizable Dashboard**: A modular and customizable interface built with React and Electron.
- **AI Integration**: Implement predictive models using TensorFlow and scikit-learn.
- **Backtesting Engine**: Test trading strategies using historical data with Backtrader.
- **Cross-platform**: Runs on Windows, macOS, and Linux.

## Installation

### Prerequisites
- [Node.js](https://nodejs.org/) (v14 or later)
- [Python](https://www.python.org/) (v3.9 or later)
- [Git](https://git-scm.com/)

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
Install dependencies and run the development server:

bash

    npm install
    npm start

###Backend Setup

    Navigate to the backend directory:

    bash

cd backend

Create a virtual environment:

bash

python -m venv env
source env/bin/activate   # On Windows: env\Scripts\activate

Install the required Python libraries:

bash

pip install -r requirements.txt

Run the FastAPI server:

bash

    uvicorn main:app --reload

Usage

    Visit the frontend at http://localhost:3000 (Electron will launch automatically).
    The backend API is available at http://127.0.0.1:8000.
    Use the /live-data/{symbol} endpoint to fetch live trading data (e.g., BTC/USDT).

Project Structure

css

trading-platform/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── ...
├── README.md
└── ...

Future Development

    Implement advanced AI models for trading signals and market predictions.
    Expand the backend to support more complex trading strategies.
    Add user authentication and portfolio management features.

Contributing

    Fork the repository.
    Create a feature branch (git checkout -b feature-branch).
    Commit changes (git commit -m 'Add new feature').
    Push the branch (git push origin feature-branch).
    Create a pull request.

