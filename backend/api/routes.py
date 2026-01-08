"""
Routes API pour le bot de trading.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["trading"])


# Ces variables seront initialisées par main.py
data_fetcher = None
signal_generator = None
paper_trader = None
portfolio = None
risk_manager = None


def set_dependencies(fetcher, signals, trader, port, risk):
    """Injecte les dépendances depuis main.py."""
    global data_fetcher, signal_generator, paper_trader, portfolio, risk_manager
    data_fetcher = fetcher
    signal_generator = signals
    paper_trader = trader
    portfolio = port
    risk_manager = risk


@router.get("/status")
async def get_status():
    """Retourne le statut général du bot."""
    return {
        "status": "running",
        "mode": "paper",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/portfolio")
async def get_portfolio():
    """Retourne le résumé du portfolio."""
    if portfolio is None:
        raise HTTPException(status_code=503, detail="Portfolio not initialized")
    return portfolio.get_summary()


@router.get("/positions")
async def get_positions():
    """Retourne les positions ouvertes."""
    if portfolio is None:
        raise HTTPException(status_code=503, detail="Portfolio not initialized")
    return {
        "positions": portfolio.get_positions_list(),
        "count": len(portfolio.positions)
    }


@router.get("/trades")
async def get_trades(limit: int = Query(default=20, le=100)):
    """Retourne l'historique des trades."""
    if portfolio is None:
        raise HTTPException(status_code=503, detail="Portfolio not initialized")
    return {
        "trades": portfolio.get_recent_trades(limit),
        "total": len(portfolio.closed_trades)
    }


@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    """Retourne le ticker pour un symbole."""
    if data_fetcher is None:
        raise HTTPException(status_code=503, detail="Data fetcher not initialized")

    symbol = symbol.upper()
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    try:
        ticker = await data_fetcher.fetch_ticker(symbol)
        return ticker
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tickers")
async def get_all_tickers():
    """Retourne tous les tickers configurés."""
    if data_fetcher is None:
        raise HTTPException(status_code=503, detail="Data fetcher not initialized")

    try:
        tickers = await data_fetcher.fetch_all_tickers()
        return {"tickers": tickers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=100, le=500)
):
    """Retourne les données OHLCV."""
    if data_fetcher is None:
        raise HTTPException(status_code=503, detail="Data fetcher not initialized")

    symbol = symbol.upper()
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    try:
        df = await data_fetcher.fetch_ohlcv(symbol, timeframe, limit)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": df.reset_index().to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/signals/{symbol}")
async def get_signals(symbol: str):
    """Génère les signaux pour un symbole."""
    if data_fetcher is None or signal_generator is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    symbol = symbol.upper()
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    try:
        df = await data_fetcher.fetch_ohlcv(symbol, "15m", 500)
        signals = signal_generator.generate_all_signals(df, symbol)
        return {
            "symbol": symbol,
            "signals": signals,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/{symbol}")
async def get_analysis(symbol: str):
    """Retourne l'analyse complète d'un symbole."""
    if data_fetcher is None or signal_generator is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    symbol = symbol.upper()
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"

    try:
        df = await data_fetcher.fetch_ohlcv(symbol, "15m", 500)
        analysis = signal_generator.get_market_analysis(df, symbol)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute")
async def execute_trade(signal: Dict):
    """Exécute un signal de trading."""
    if paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")

    try:
        result = await paper_trader.execute_signal(signal)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/close/{position_id}")
async def close_position(position_id: str, current_price: float = Query(...)):
    """Ferme une position manuellement."""
    if paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")

    try:
        result = await paper_trader.close_position_manual(position_id, current_price)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/close-all")
async def close_all_positions():
    """Ferme toutes les positions ouvertes."""
    if paper_trader is None or data_fetcher is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        tickers = await data_fetcher.fetch_all_tickers()
        prices = {t['symbol']: t['last'] for t in tickers.values()}
        results = await paper_trader.close_all_positions(prices)
        return {"closed_positions": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/risk")
async def get_risk_status():
    """Retourne le statut du risque."""
    if risk_manager is None or portfolio is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    return risk_manager.get_risk_summary(portfolio.capital)


@router.get("/performance")
async def get_performance():
    """Retourne les métriques de performance."""
    if paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")

    return paper_trader.get_performance_metrics()


@router.get("/config")
async def get_config():
    """Retourne la configuration actuelle (sans les secrets)."""
    from backend.config import CONFIG

    # Retourner une version sanitisée de la config
    return {
        "mode": CONFIG.get("mode", "paper"),
        "symbols": CONFIG.get("symbols", []),
        "timeframes": CONFIG.get("timeframes", {}),
        "risk_management": {
            "max_risk_per_trade": CONFIG.get("risk_management", {}).get("max_risk_per_trade"),
            "max_risk_per_day": CONFIG.get("risk_management", {}).get("max_risk_per_day"),
            "max_open_positions": CONFIG.get("risk_management", {}).get("max_open_positions")
        },
        "strategies": {
            k: {"enabled": v.get("enabled", False)}
            for k, v in CONFIG.get("strategies", {}).items()
        }
    }
