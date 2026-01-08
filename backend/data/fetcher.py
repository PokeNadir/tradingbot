"""
Module de récupération des données de marché via CCXT.

Fonctionnalités:
- Récupération OHLCV multi-timeframes
- Cache des données
- Gestion des erreurs et rate limiting
"""

import ccxt
import pandas as pd
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Récupère les données de marché depuis les exchanges.

    Attributes:
        exchange_id: Identifiant de l'exchange (binance, coinbase, etc.)
        exchange: Instance CCXT de l'exchange
        symbols: Liste des paires à suivre
        data_cache: Cache des données OHLCV
    """

    def __init__(self, config: dict):
        """
        Initialise le DataFetcher.

        Args:
            config: Configuration contenant exchange.name, exchange.testnet, symbols
        """
        self.config = config
        self.exchange_id = config.get('exchange', {}).get('name', 'binance')
        self.symbols = config.get('symbols', ['BTC/USDT'])
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.exchange = self._init_exchange()

    def _init_exchange(self):
        """Initialise la connexion à l'exchange."""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            exchange = exchange_class({
                'enableRateLimit': self.config.get('exchange', {}).get('rate_limit', True),
                'options': {'defaultType': 'spot'}
            })

            if self.config.get('exchange', {}).get('testnet', True):
                if hasattr(exchange, 'set_sandbox_mode'):
                    exchange.set_sandbox_mode(True)
                    logger.info(f"Mode testnet activé pour {self.exchange_id}")

            return exchange
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '15m',
        limit: int = 500
    ) -> pd.DataFrame:
        """
        Récupère les données OHLCV pour un symbole.

        Args:
            symbol: Paire de trading (ex: 'BTC/USDT')
            timeframe: Intervalle ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Nombre de bougies

        Returns:
            DataFrame avec timestamp, open, high, low, close, volume
        """
        try:
            ohlcv = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                symbol,
                timeframe,
                limit=limit
            )

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            cache_key = f"{symbol}_{timeframe}"
            self.data_cache[cache_key] = df

            logger.debug(f"Récupéré {len(df)} bougies pour {symbol} {timeframe}")
            return df

        except Exception as e:
            logger.error(f"Erreur fetch_ohlcv {symbol}: {e}")
            raise

    async def fetch_multi_timeframe(
        self,
        symbol: str,
        timeframes: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Récupère les données pour plusieurs timeframes.

        Args:
            symbol: Paire de trading
            timeframes: Liste des timeframes (défaut: config)

        Returns:
            Dict avec timeframe comme clé et DataFrame comme valeur
        """
        if timeframes is None:
            tf_config = self.config.get('timeframes', {})
            timeframes = [
                tf_config.get('primary', '15m'),
                tf_config.get('confirmation', '1h'),
                tf_config.get('trend', '4h')
            ]

        tasks = [self.fetch_ohlcv(symbol, tf) for tf in timeframes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = {}
        for tf, result in zip(timeframes, results):
            if not isinstance(result, Exception):
                data[tf] = result
            else:
                logger.error(f"Erreur fetch {symbol} {tf}: {result}")

        return data

    async def fetch_ticker(self, symbol: str) -> dict:
        """
        Récupère le ticker actuel.

        Args:
            symbol: Paire de trading

        Returns:
            Dictionnaire avec prix, volume, etc.
        """
        try:
            ticker = await asyncio.to_thread(
                self.exchange.fetch_ticker,
                symbol
            )
            return {
                'symbol': symbol,
                'last': ticker.get('last', 0),
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'high_24h': ticker.get('high', 0),
                'low_24h': ticker.get('low', 0),
                'volume_24h': ticker.get('baseVolume', 0),
                'change_24h': ticker.get('percentage', 0),
                'spread': ((ticker.get('ask', 0) - ticker.get('bid', 0)) / ticker.get('last', 1)
                          if ticker.get('last') else 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur fetch_ticker {symbol}: {e}")
            raise

    async def fetch_all_tickers(self) -> Dict[str, dict]:
        """Récupère les tickers pour tous les symboles configurés."""
        tasks = [self.fetch_ticker(symbol) for symbol in self.symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        tickers = {}
        for symbol, result in zip(self.symbols, results):
            if not isinstance(result, Exception):
                tickers[symbol] = result
            else:
                logger.error(f"Erreur ticker {symbol}: {result}")

        return tickers

    async def fetch_order_book(self, symbol: str, limit: int = 20) -> dict:
        """
        Récupère le carnet d'ordres.

        Args:
            symbol: Paire de trading
            limit: Profondeur du carnet

        Returns:
            Dict avec bids, asks, spread
        """
        try:
            order_book = await asyncio.to_thread(
                self.exchange.fetch_order_book,
                symbol,
                limit
            )

            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])

            best_bid = bids[0][0] if bids else 0
            best_ask = asks[0][0] if asks else 0
            spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0

            # Calculate Order Book Imbalance
            bid_volume = sum(b[1] for b in bids)
            ask_volume = sum(a[1] for a in asks)
            total_volume = bid_volume + ask_volume
            obi = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0

            return {
                'symbol': symbol,
                'bids': bids[:10],
                'asks': asks[:10],
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread': spread,
                'spread_percent': spread * 100,
                'obi': obi,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur fetch_order_book {symbol}: {e}")
            raise

    def get_cached_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Récupère les données en cache."""
        cache_key = f"{symbol}_{timeframe}"
        return self.data_cache.get(cache_key)

    def clear_cache(self):
        """Vide le cache de données."""
        self.data_cache.clear()
        logger.info("Cache vidé")
