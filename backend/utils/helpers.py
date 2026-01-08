"""
Fonctions utilitaires pour le bot de trading.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import hashlib


def round_price(price: float, tick_size: float = 0.01) -> float:
    """
    Arrondit un prix au tick size le plus proche.

    Args:
        price: Prix à arrondir
        tick_size: Taille du tick (ex: 0.01 pour 2 décimales)

    Returns:
        Prix arrondi
    """
    return round(price / tick_size) * tick_size


def round_size(size: float, step_size: float = 0.001) -> float:
    """
    Arrondit une taille de position au step size.

    Args:
        size: Taille à arrondir
        step_size: Pas de quantité

    Returns:
        Taille arrondie
    """
    return round(size / step_size) * step_size


def calculate_pnl(
    entry_price: float,
    exit_price: float,
    size: float,
    direction: str,
    fees_percent: float = 0.001
) -> Dict[str, float]:
    """
    Calcule le P&L d'un trade.

    Args:
        entry_price: Prix d'entrée
        exit_price: Prix de sortie
        size: Taille de la position
        direction: 'long' ou 'short'
        fees_percent: Frais en pourcentage (0.001 = 0.1%)

    Returns:
        Dict avec gross_pnl, fees, net_pnl, pnl_percent
    """
    if direction.lower() == 'long':
        gross_pnl = (exit_price - entry_price) * size
    else:
        gross_pnl = (entry_price - exit_price) * size

    # Frais d'entrée et de sortie
    entry_value = entry_price * size
    exit_value = exit_price * size
    fees = (entry_value + exit_value) * fees_percent

    net_pnl = gross_pnl - fees
    pnl_percent = (net_pnl / entry_value) * 100 if entry_value > 0 else 0

    return {
        'gross_pnl': round(gross_pnl, 2),
        'fees': round(fees, 2),
        'net_pnl': round(net_pnl, 2),
        'pnl_percent': round(pnl_percent, 4)
    }


def timeframe_to_seconds(timeframe: str) -> int:
    """
    Convertit un timeframe en secondes.

    Args:
        timeframe: Timeframe (ex: '1m', '5m', '1h', '4h', '1d')

    Returns:
        Nombre de secondes
    """
    multipliers = {
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }

    unit = timeframe[-1]
    value = int(timeframe[:-1])

    return value * multipliers.get(unit, 60)


def seconds_to_timeframe(seconds: int) -> str:
    """
    Convertit des secondes en timeframe.

    Args:
        seconds: Nombre de secondes

    Returns:
        Timeframe string
    """
    if seconds >= 604800:
        return f"{seconds // 604800}w"
    elif seconds >= 86400:
        return f"{seconds // 86400}d"
    elif seconds >= 3600:
        return f"{seconds // 3600}h"
    else:
        return f"{seconds // 60}m"


def is_market_open(symbol: str, timestamp: datetime = None) -> bool:
    """
    Vérifie si le marché est ouvert (pour crypto = toujours vrai).

    Args:
        symbol: Symbole à vérifier
        timestamp: Timestamp à vérifier (défaut: maintenant)

    Returns:
        True si le marché est ouvert
    """
    # Crypto markets sont toujours ouverts
    if 'USDT' in symbol or 'BTC' in symbol or 'ETH' in symbol:
        return True

    # Pour les marchés traditionnels, implémenter la logique ici
    return True


def get_kill_zone(timestamp: datetime = None) -> Optional[str]:
    """
    Détermine la kill zone actuelle (ICT concept).

    Kill Zones (EST):
    - London: 2:00-5:00 AM
    - New York: 7:00-10:00 AM
    - Silver Bullet: 10:00-11:00 AM

    Args:
        timestamp: Timestamp à vérifier (défaut: maintenant)

    Returns:
        Nom de la kill zone ou None
    """
    if timestamp is None:
        timestamp = datetime.now()

    hour = timestamp.hour
    minute = timestamp.minute
    current_time = hour * 60 + minute

    # London: 2:00-5:00 AM EST
    if 2 * 60 <= current_time < 5 * 60:
        return "London"

    # NY: 7:00-10:00 AM EST
    if 7 * 60 <= current_time < 10 * 60:
        return "New York"

    # Silver Bullet: 10:00-11:00 AM EST
    if 10 * 60 <= current_time < 11 * 60:
        return "Silver Bullet"

    return None


def generate_trade_id(
    symbol: str,
    timestamp: datetime,
    direction: str
) -> str:
    """
    Génère un ID unique pour un trade.

    Args:
        symbol: Symbole tradé
        timestamp: Timestamp du trade
        direction: Direction du trade

    Returns:
        ID unique du trade
    """
    data = f"{symbol}{timestamp.isoformat()}{direction}"
    return hashlib.sha256(data.encode()).hexdigest()[:12]


def format_currency(value: float, currency: str = "USDT") -> str:
    """
    Formate une valeur monétaire.

    Args:
        value: Valeur à formater
        currency: Devise

    Returns:
        Valeur formatée
    """
    if abs(value) >= 1000000:
        return f"{value/1000000:.2f}M {currency}"
    elif abs(value) >= 1000:
        return f"{value/1000:.2f}K {currency}"
    else:
        return f"{value:.2f} {currency}"


def format_percent(value: float) -> str:
    """
    Formate un pourcentage.

    Args:
        value: Valeur décimale (0.05 = 5%)

    Returns:
        Pourcentage formaté
    """
    return f"{value * 100:+.2f}%"


def resample_ohlcv(
    df: pd.DataFrame,
    target_timeframe: str
) -> pd.DataFrame:
    """
    Resample des données OHLCV vers un timeframe plus grand.

    Args:
        df: DataFrame avec colonnes OHLCV et index timestamp
        target_timeframe: Timeframe cible (ex: '1h', '4h')

    Returns:
        DataFrame resamplé
    """
    # Mapping pandas resample rules
    rule_map = {
        '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
        '1h': '1H', '4h': '4H', '1d': '1D', '1w': '1W'
    }

    rule = rule_map.get(target_timeframe, target_timeframe)

    resampled = df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    return resampled


def validate_ohlcv(df: pd.DataFrame) -> bool:
    """
    Valide un DataFrame OHLCV.

    Args:
        df: DataFrame à valider

    Returns:
        True si valide
    """
    required_columns = ['open', 'high', 'low', 'close', 'volume']

    # Vérifier les colonnes
    if not all(col in df.columns for col in required_columns):
        return False

    # Vérifier les valeurs
    if df.isnull().any().any():
        return False

    # Vérifier high >= low
    if not (df['high'] >= df['low']).all():
        return False

    # Vérifier high >= open et close
    if not ((df['high'] >= df['open']) & (df['high'] >= df['close'])).all():
        return False

    # Vérifier low <= open et close
    if not ((df['low'] <= df['open']) & (df['low'] <= df['close'])).all():
        return False

    return True
