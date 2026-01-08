# Algorithmic Trading Bot

A comprehensive algorithmic trading bot with Python backend and React frontend, featuring technical analysis, Smart Money Concepts (ICT), and paper trading capabilities.

## Features

### Technical Analysis
- **Indicators**: RSI, MACD, Bollinger Bands, ATR, EMAs, ADX, Stochastic
- **Candlestick Patterns**: Hammer, Engulfing, Morning/Evening Star, Doji
- **Divergence Detection**: RSI and MACD divergences (regular and hidden)

### Smart Money Concepts (ICT)
- Swing Highs/Lows identification
- Order Blocks (Bullish/Bearish)
- Fair Value Gaps (FVG)
- Break of Structure (BOS)
- Change of Character (CHoCH)
- Kill Zones (London, New York, Silver Bullet)

### Trading Strategies
- **Mean Reversion**: Bollinger Bands + RSI
- **EMA Crossover**: 9/21 EMA with ADX confirmation
- **Breakout**: Support/Resistance breakout with volume
- **Grid Trading**: For ranging markets
- **Smart DCA**: RSI-triggered dollar cost averaging

### Risk Management
- Position sizing (Kelly Criterion, fixed percentage)
- ATR-based stop loss and take profit
- Scaling out (33%/33%/34% at 1R/2R/3R)
- Daily loss limits and drawdown protection
- Pre-trade checks

### Frontend Dashboard
- Real-time price charts with indicators
- Trade signals with one-click execution
- Portfolio tracking
- Position management
- On-chain metrics display
- Market structure visualization

## Project Structure

```
trading-bot/
├── backend/
│   ├── api/           # FastAPI routes and WebSocket
│   ├── data/          # Data fetching and storage
│   ├── indicators/    # Technical indicators and SMC
│   ├── strategies/    # Trading strategies
│   ├── trading/       # Paper trading and risk management
│   ├── analysis/      # Market structure analysis
│   └── utils/         # Logging and helpers
├── frontend/
│   └── src/
│       ├── components/  # React components
│       ├── hooks/       # Custom hooks
│       └── utils/       # Utilities
├── config/
│   └── config.yaml    # Configuration file
├── tests/             # Test suite
└── data/              # Database storage
```

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration as needed
nano config/config.yaml
```

## Running the Application

### Development Mode

```bash
# Terminal 1: Backend
source venv/bin/activate
python -m backend.main

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Docker

```bash
docker-compose up -d
```

### Access

- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Configuration

Key configuration options in `config/config.yaml`:

### Trading Mode
```yaml
mode: "paper"  # "paper" or "live"
```

### Risk Management
```yaml
risk_management:
  max_risk_per_trade: 0.01  # 1% max per trade
  max_risk_per_day: 0.03    # 3% daily loss limit
  max_open_positions: 3
```

### Strategies
```yaml
strategies:
  mean_reversion:
    enabled: true
  ema_crossover:
    enabled: true
  breakout:
    enabled: true
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/portfolio` | GET | Get portfolio summary |
| `/api/positions` | GET | Get open positions |
| `/api/trades` | GET | Get trade history |
| `/api/signals/{symbol}` | GET | Get trading signals |
| `/api/execute` | POST | Execute a trade |
| `/api/close/{id}` | POST | Close a position |
| `/ws/{symbol}` | WS | Real-time data stream |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_indicators.py -v

# Run with coverage
pytest tests/ --cov=backend
```

## Risk Disclaimer

This software is for educational and paper trading purposes only. Trading cryptocurrencies carries significant risk. Never invest more than you can afford to lose.

**Important Rules:**
- Always test strategies thoroughly before any live trading
- Never risk more than 1-2% per trade
- Maintain proper position sizing
- Use stop-losses on every trade
- Monitor drawdown limits

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
