"""
Main entry point for the Trading Bot API.
FastAPI application avec WebSocket pour les updates temps réel.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import CONFIG
from backend.api.routes import router
from backend.api.websocket import ConnectionManager
from backend.data.fetcher import DataFetcher
from backend.data.database import Database
from backend.indicators.technical import TechnicalIndicators
from backend.indicators.patterns import PatternDetector
from backend.indicators.divergences import DivergenceDetector
from backend.indicators.smc import SmartMoneyConcepts
from backend.indicators.signals import SignalGenerator
from backend.trading.paper_trader import PaperTrader
from backend.trading.risk_manager import RiskManager
from backend.trading.portfolio import Portfolio
from backend.utils.logger import logger


# Global instances
manager = ConnectionManager()
data_fetcher = None
paper_trader = None
portfolio = None
signal_generator = None
background_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application.
    Initialise les composants au démarrage, les nettoie à l'arrêt.
    """
    global data_fetcher, paper_trader, portfolio, signal_generator

    logger.info("Starting Trading Bot...")

    # Initialize components
    try:
        data_fetcher = DataFetcher(CONFIG)
        risk_manager = RiskManager(CONFIG)
        portfolio = Portfolio(CONFIG)
        paper_trader = PaperTrader(CONFIG, portfolio, risk_manager)

        # Initialize signal generator with all indicator modules
        technical = TechnicalIndicators(CONFIG)
        patterns = PatternDetector(CONFIG)
        divergences = DivergenceDetector(CONFIG)
        smc = SmartMoneyConcepts(CONFIG)

        signal_generator = SignalGenerator(
            CONFIG, technical, patterns, divergences, smc
        )

        # Initialize database
        db = Database(CONFIG)
        await db.init()

        logger.info(f"Trading Bot initialized for symbols: {CONFIG.get('symbols', [])}")
        logger.info(f"Mode: {CONFIG.get('mode', 'paper')}")
        logger.info(f"Initial capital: {CONFIG.get('paper_trading', {}).get('initial_capital', 10000)} USDT")

        # Start background data fetching task
        task = asyncio.create_task(data_update_loop())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    except Exception as e:
        logger.error(f"Failed to initialize trading bot: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down Trading Bot...")
    for task in background_tasks:
        task.cancel()


async def data_update_loop():
    """
    Boucle de mise à jour des données en arrière-plan.
    Récupère les données, calcule les indicateurs, génère les signaux.
    """
    update_interval = CONFIG.get('data', {}).get('update_interval', 5)

    while True:
        try:
            for symbol in CONFIG.get('symbols', []):
                # Fetch data for all timeframes
                try:
                    data = await data_fetcher.fetch_multi_timeframe(symbol)
                except Exception as fetch_error:
                    logger.warning(f"Failed to fetch data for {symbol}: {fetch_error}")
                    continue

                if data:
                    # Generate signals on primary timeframe
                    primary_tf = CONFIG.get('timeframes', {}).get('primary', '15m')
                    if primary_tf in data:
                        df = data[primary_tf]

                        # Vérifier que le DataFrame a assez de données
                        if df is None or df.empty or len(df) < 50:
                            logger.debug(f"Not enough data for {symbol}: {len(df) if df is not None else 0} rows")
                            continue

                        try:
                            signals = signal_generator.generate_all_signals(df.copy(), symbol)
                        except Exception as signal_error:
                            logger.warning(f"Failed to generate signals for {symbol}: {signal_error}")
                            signals = []

                        # Check for trade proposals
                        for signal in signals:
                            if signal.get('strength', 0) >= 0.7:
                                logger.info(
                                    f"Strong signal: {signal.get('type')} on {symbol} "
                                    f"({signal.get('strength', 0):.0%})"
                                )

                        # Broadcast to WebSocket clients
                        try:
                            ticker = await data_fetcher.fetch_ticker(symbol)
                        except Exception as ticker_error:
                            logger.warning(f"Failed to fetch ticker for {symbol}: {ticker_error}")
                            ticker = {'symbol': symbol, 'last': 0}

                        await manager.broadcast({
                            'type': 'update',
                            'symbol': symbol,
                            'ticker': ticker,
                            'signals': signals,
                            'portfolio': portfolio.get_summary() if portfolio else {}
                        })

            await asyncio.sleep(update_interval)

        except Exception as e:
            logger.error(f"Error in data update loop: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            await asyncio.sleep(update_interval)


# Create FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="Bot de trading algorithmique avec indicateurs techniques et Smart Money Concepts",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.get('api', {}).get('cors_origins', ["http://localhost:5173"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint pour les updates temps réel.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            if data.get('type') == 'subscribe':
                symbols = data.get('symbols', CONFIG.get('symbols', []))
                await websocket.send_json({
                    'type': 'subscribed',
                    'symbols': symbols
                })

            elif data.get('type') == 'execute_trade':
                # Execute a trade proposal
                if paper_trader:
                    result = await paper_trader.execute_signal(data.get('signal'))
                    await websocket.send_json({
                        'type': 'trade_result',
                        'result': result
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "mode": CONFIG.get('mode', 'paper'),
        "symbols": CONFIG.get('symbols', []),
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "data_fetcher": data_fetcher is not None,
            "paper_trader": paper_trader is not None,
            "portfolio": portfolio is not None,
            "signal_generator": signal_generator is not None
        }
    }


def start():
    """Start the API server."""
    host = CONFIG.get('api', {}).get('host', '0.0.0.0')
    port = CONFIG.get('api', {}).get('port', 8000)

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    start()
