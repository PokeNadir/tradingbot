"""
Module de récupération des données de marché via CCXT.

Fonctionnalités:
- Récupération OHLCV multi-timeframes
- Cache des données
- Gestion des erreurs et rate limiting
- Retry automatique avec backoff exponentiel
"""

import ccxt
import pandas as pd
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging
import time

logger = logging.getLogger(__name__)

# Nombre de tentatives pour les requêtes API
MAX_RETRIES = 3
RETRY_DELAY = 2  # secondes


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
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                },
                'timeout': 30000,  # 30 secondes timeout
            })

            # Mode testnet seulement si explicitement activé
            use_testnet = self.config.get('exchange', {}).get('testnet', False)
            if use_testnet:
                if hasattr(exchange, 'set_sandbox_mode'):
                    exchange.set_sandbox_mode(True)
                    logger.info(f"Mode testnet activé pour {self.exchange_id}")
            else:
                logger.info(f"Connexion à {self.exchange_id} (API réelle - données publiques)")

            # Charger les marchés
            exchange.load_markets()
            logger.info(f"Marchés chargés: {len(exchange.markets)} paires disponibles")

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
        Récupère les données OHLCV pour un symbole avec retry automatique.

        Args:
            symbol: Paire de trading (ex: 'BTC/USDT')
            timeframe: Intervalle ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Nombre de bougies

        Returns:
            DataFrame avec timestamp, open, high, low, close, volume
        """
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                ohlcv = await asyncio.to_thread(
                    self.exchange.fetch_ohlcv,
                    symbol,
                    timeframe,
                    limit=limit
                )

                if not ohlcv or len(ohlcv) == 0:
                    logger.warning(f"Aucune donnée reçue pour {symbol} {timeframe}")
                    return pd.DataFrame()

                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)

                # Vérifier la qualité des données
                if df['close'].isna().any():
                    logger.warning(f"Données incomplètes pour {symbol} {timeframe}")

                cache_key = f"{symbol}_{timeframe}"
                self.data_cache[cache_key] = df

                logger.info(f"✓ {symbol} {timeframe}: {len(df)} bougies (dernière: {df.index[-1]})")
                return df

            except ccxt.NetworkError as e:
                last_error = e
                logger.warning(f"Erreur réseau {symbol} (tentative {attempt + 1}/{MAX_RETRIES}): {e}")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

            except ccxt.ExchangeError as e:
                last_error = e
                logger.error(f"Erreur exchange {symbol}: {e}")
                break  # Ne pas réessayer pour les erreurs d'exchange

            except Exception as e:
                last_error = e
                logger.warning(f"Erreur {symbol} (tentative {attempt + 1}/{MAX_RETRIES}): {e}")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        logger.error(f"Échec fetch_ohlcv {symbol} après {MAX_RETRIES} tentatives: {last_error}")
        return pd.DataFrame()

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
        Récupère le ticker actuel avec retry automatique.

        Args:
            symbol: Paire de trading

        Returns:
            Dictionnaire avec prix, volume, etc.
        """
        for attempt in range(MAX_RETRIES):
            try:
                ticker = await asyncio.to_thread(
                    self.exchange.fetch_ticker,
                    symbol
                )

                last_price = ticker.get('last', 0) or 0
                bid_price = ticker.get('bid', 0) or 0
                ask_price = ticker.get('ask', 0) or 0

                spread = 0
                if last_price > 0 and bid_price > 0 and ask_price > 0:
                    spread = (ask_price - bid_price) / last_price

                return {
                    'symbol': symbol,
                    'last': last_price,
                    'bid': bid_price,
                    'ask': ask_price,
                    'high_24h': ticker.get('high', 0) or 0,
                    'low_24h': ticker.get('low', 0) or 0,
                    'volume_24h': ticker.get('baseVolume', 0) or 0,
                    'change_24h': ticker.get('percentage', 0) or 0,
                    'spread': spread,
                    'timestamp': datetime.now().isoformat()
                }

            except ccxt.NetworkError as e:
                logger.warning(f"Erreur réseau ticker {symbol} (tentative {attempt + 1}): {e}")
                await asyncio.sleep(RETRY_DELAY)

            except Exception as e:
                logger.warning(f"Erreur ticker {symbol}: {e}")
                break

        # Retourner des valeurs par défaut en cas d'échec
        return {
            'symbol': symbol,
            'last': 0,
            'bid': 0,
            'ask': 0,
            'high_24h': 0,
            'low_24h': 0,
            'volume_24h': 0,
            'change_24h': 0,
            'spread': 0,
            'timestamp': datetime.now().isoformat(),
            'error': True
        }

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
