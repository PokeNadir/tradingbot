# CLAUDE.md - Bot de Trading Algorithmique avec Interface React

## 🎯 Objectif du Projet

Créer un **bot de trading algorithmique complet** avec:
1. **Backend Python** - Récupération de données, indicateurs techniques, Smart Money Concepts, analyse on-chain, paper trading
2. **Frontend React** - Dashboard interactif avec propositions de trades automatiques
3. **API FastAPI** - Communication backend/frontend en temps réel

---

## 📚 Guide de Référence des Stratégies

Ce projet s'appuie sur le fichier **`TRADING_STRATEGIES_GUIDE.md`** qui contient:
- Configuration optimale des indicateurs techniques
- Stratégies quantitatives programmables
- Analyse on-chain et métriques institutionnelles
- Gestion avancée du risque
- Concepts ICT/Smart Money détaillés
- Règles de backtesting et optimisation

**⚠️ IMPORTANT:** Toujours consulter ce guide pour les paramètres et règles de trading.

---

## 📁 Structure du Projet à Créer

```
trading-bot/
├── CLAUDE.md
├── TRADING_STRATEGIES_GUIDE.md    # Guide de référence des stratégies
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── requirements.txt
│
├── config/
│   └── config.yaml
│
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration loader
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # API endpoints
│   │   └── websocket.py           # WebSocket handlers
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetcher.py             # CCXT data fetcher
│   │   ├── database.py            # SQLite storage
│   │   └── onchain.py             # Analyse on-chain (Glassnode, etc.)
│   │
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── technical.py           # RSI, MACD, Bollinger, ATR, ADX
│   │   ├── patterns.py            # Patterns de chandeliers japonais
│   │   ├── smc.py                 # Smart Money Concepts (ICT)
│   │   ├── divergences.py         # Détection de divergences RSI/MACD
│   │   └── signals.py             # Signal generator
│   │
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base_strategy.py       # Classe de base pour stratégies
│   │   ├── mean_reversion.py      # Stratégie Mean Reversion (BB + RSI)
│   │   ├── ema_crossover.py       # Stratégie EMA Crossover
│   │   ├── breakout.py            # Stratégie Breakout avec volume
│   │   ├── grid_trading.py        # Grid Trading pour marchés ranging
│   │   └── dca_smart.py           # DCA intelligent avec triggers
│   │
│   ├── trading/
│   │   ├── __init__.py
│   │   ├── paper_trader.py        # Paper trading engine
│   │   ├── risk_manager.py        # Position sizing, Kelly, drawdown
│   │   ├── portfolio.py           # Portfolio tracking
│   │   └── pre_trade_checks.py    # Vérifications pré-trade
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── market_structure.py    # BOS, CHoCH, structure de marché
│   │   ├── manipulation.py        # Détection spoofing, OBI
│   │   └── volume_profile.py      # POC, Value Area
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   │
│   ├── public/
│   │   └── favicon.ico
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       │
│       ├── components/
│       │   ├── Dashboard.jsx       # Main dashboard
│       │   ├── PriceChart.jsx      # Price chart with indicators
│       │   ├── TradeProposal.jsx   # Trade proposal cards
│       │   ├── IndicatorGauge.jsx  # Indicator gauges
│       │   ├── Portfolio.jsx       # Portfolio summary
│       │   ├── TradeHistory.jsx    # Trade history list
│       │   ├── OnChainMetrics.jsx  # Métriques on-chain (MVRV, NUPL)
│       │   └── MarketStructure.jsx # Visualisation SMC
│       │
│       ├── hooks/
│       │   ├── useWebSocket.js     # WebSocket hook
│       │   └── useTrading.js       # Trading state hook
│       │
│       └── utils/
│           ├── api.js              # API client
│           └── calculations.js     # Frontend calculations
│
├── data/
│   └── .gitkeep
│
└── tests/
    ├── __init__.py
    ├── test_indicators.py
    ├── test_signals.py
    ├── test_strategies.py
    ├── test_risk_manager.py
    └── test_paper_trader.py
```

---

## 📦 Fichiers de Configuration

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.env

# Node
node_modules/
dist/
.vite/

# IDE
.vscode/
.idea/

# Data
data/*.db
data/*.json
*.log

# OS
.DS_Store
Thumbs.db
```

### .env.example

```env
# Trading Configuration
EXCHANGE=binance
TESTNET=true

# API Keys (optionnel pour paper trading)
API_KEY=
API_SECRET=

# Paper Trading
INITIAL_CAPITAL=10000
CURRENCY=USDT

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Database
DATABASE_URL=sqlite:///data/trades.db

# On-Chain APIs (optionnel)
GLASSNODE_API_KEY=
COINGLASS_API_KEY=
```

### requirements.txt

```txt
# Core
python-dotenv>=1.0.0
pyyaml>=6.0

# Web Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# WebSocket
websockets>=12.0

# Exchange API
ccxt>=4.2.0

# Data Processing
pandas>=2.0.0
numpy>=1.24.0

# Technical Analysis
ta>=0.11.0

# Database
sqlalchemy>=2.0.0
aiosqlite>=0.19.0

# Async
aiohttp>=3.9.0

# Logging & CLI
rich>=13.0.0
click>=8.0.0

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.26.0
```

### config/config.yaml

```yaml
# ============================================================================
# Configuration principale du bot de trading
# Référence: TRADING_STRATEGIES_GUIDE.md pour les détails des paramètres
# ============================================================================

# Mode de fonctionnement
mode: "paper"  # "paper" ou "live"

# Capital initial
paper_trading:
  initial_capital: 10000
  currency: "USDT"

# Exchange configuration
exchange:
  name: "binance"
  testnet: true
  rate_limit: true

# Symboles à trader
symbols:
  - "BTC/USDT"
  - "ETH/USDT"
  - "SOL/USDT"

# Timeframes (Multi-Timeframe Analysis)
timeframes:
  primary: "15m"       # Timeframe d'exécution
  confirmation: "1h"   # Confirmation de tendance
  trend: "4h"          # Biais de tendance HTF

# ============================================================================
# INDICATEURS TECHNIQUES
# Paramètres optimisés selon le Guide de Stratégies
# ============================================================================
indicators:
  # RSI - Relative Strength Index
  rsi:
    period: 14
    overbought: 70        # Standard
    oversold: 30          # Standard
    overbought_crypto: 80 # Pour crypto volatile
    oversold_crypto: 20   # Pour crypto volatile
  
  # MACD - Moving Average Convergence Divergence
  macd:
    fast: 12
    slow: 26
    signal: 9
  
  # Bollinger Bands
  bollinger:
    period: 20
    std_dev: 2.0
    squeeze_threshold: 0.75  # BBW < SMA(BBW,50) × 0.75 = squeeze
  
  # ATR - Average True Range
  atr:
    period: 14
  
  # EMAs - Exponential Moving Averages
  ema:
    fast: 9              # Scalping/Momentum
    slow: 21             # Day trading
    trend: 50            # Moyen terme
    long_trend: 200      # Long terme (SMA recommandé)
  
  # ADX - Average Directional Index
  adx:
    period: 14
    threshold: 25        # ADX > 25 = marché en tendance
  
  # Stochastic
  stochastic:
    k_period: 14
    d_period: 3
    overbought: 80
    oversold: 20

# ============================================================================
# SMART MONEY CONCEPTS (ICT)
# ============================================================================
smc:
  swing_length: 10
  fvg_min_size: 0.001          # Taille minimale FVG (0.1%)
  ob_volume_threshold: 1.5     # Volume OB > 1.5× volume moyen
  displacement_atr: 2.0        # Displacement = move > ATR × 2
  liquidity_range: 0.01        # 1% pour identifier liquidité
  
  # Kill Zones (heures optimales - EST)
  kill_zones:
    london_open: "02:00"       # 2:00-5:00 AM EST
    london_close: "05:00"
    ny_open: "07:00"           # 7:00-10:00 AM EST
    ny_close: "10:00"
    silver_bullet: "10:00"     # 10:00-11:00 AM EST
    silver_bullet_end: "11:00"

# ============================================================================
# PATTERNS DE CHANDELIERS
# ============================================================================
patterns:
  hammer:
    body_ratio: 0.5            # Corps ≤ 50% du range
    lower_wick_ratio: 2.0      # Mèche inf ≥ 2× corps
    upper_wick_max: 0.1        # Mèche sup ≤ 10% du range
  
  engulfing:
    min_body_ratio: 0.6        # Le corps doit être significatif
  
  doji:
    body_max_ratio: 0.05       # Corps ≤ 5% du range

# ============================================================================
# FIBONACCI
# ============================================================================
fibonacci:
  retracement_levels: [0.236, 0.382, 0.5, 0.618, 0.786]
  extension_levels: [1.272, 1.618, 2.0, 2.618]
  golden_ratio: 0.618          # Niveau le plus important

# ============================================================================
# GESTION DES RISQUES
# Règles ABSOLUES - Ne jamais dépasser ces limites
# ============================================================================
risk_management:
  # Position Sizing
  max_risk_per_trade: 0.01     # 1% max par trade (RECOMMANDÉ)
  max_risk_per_trade_max: 0.02 # 2% MAXIMUM ABSOLU
  max_risk_per_day: 0.03       # 3% perte max journalière
  max_risk_total: 0.06         # 6% exposition totale max
  max_open_positions: 3
  default_leverage: 1
  
  # Kelly Criterion
  kelly_fraction: 0.25         # Utiliser 25% du Kelly (Quarter-Kelly)
  
  # Stop Loss (basé sur ATR)
  stop_loss:
    type: "atr"
    atr_multiplier_day: 1.5    # Day trading: 1.5-2.0× ATR
    atr_multiplier_swing: 2.0  # Swing trading: 2.0-2.5× ATR
    atr_multiplier_position: 2.5 # Position trading: 2.5-3.0× ATR
    atr_multiplier_volatile: 3.0 # Haute volatilité: 3.0-4.0× ATR
    fixed_percent: 0.02        # Fallback: 2%
  
  # Take Profit
  take_profit:
    min_risk_reward_ratio: 2.0 # Minimum R:R de 2:1
    trailing_stop: true
    trailing_atr_multiplier: 1.0
    
    # Scaling out progressif
    scaling_out:
      enabled: true
      level_1_percent: 0.33    # 33% à 1R
      level_1_r: 1.0
      level_2_percent: 0.33    # 33% à 2R
      level_2_r: 2.0
      level_3_percent: 0.34    # 34% trailing
  
  # Limites de Drawdown
  drawdown:
    daily_loss_limit: 0.03     # Stop trading si perte > 3% jour
    weekly_loss_limit: 0.06    # Réduire taille 50% si > 6% semaine
    max_drawdown: 0.15         # PAUSE TOTALE si > 15%
    consecutive_loss_pause: 3  # Pause après 3 pertes consécutives
    pause_duration_minutes: 15 # Durée de pause minimum

# ============================================================================
# STRATÉGIES DE TRADING
# ============================================================================
strategies:
  # Mean Reversion (Bollinger + RSI)
  mean_reversion:
    enabled: true
    entry_conditions:
      long: "price < bb_lower AND rsi < 30"
      short: "price > bb_upper AND rsi > 70"
    target: "bb_middle"
    stop_atr_multiplier: 1.5
  
  # EMA Crossover
  ema_crossover:
    enabled: true
    fast_ema: 9
    slow_ema: 21
    adx_threshold: 25
    rsi_filter_long: 50        # RSI > 50 pour long
    rsi_filter_short: 50       # RSI < 50 pour short
    stop_atr_multiplier: 2.0
    min_risk_reward: 2.0
  
  # Breakout
  breakout:
    enabled: true
    lookback_period: 20        # rolling_max/min sur 20 périodes
    volume_multiplier: 1.5     # Volume > avg × 1.5
    adx_confirmation: true     # ADX rising vers 25-40
    stop_atr_multiplier: 1.5
  
  # Grid Trading
  grid_trading:
    enabled: false             # Activer manuellement pour ranging
    num_grids: 20
    grid_type: "geometric"     # "arithmetic" ou "geometric"
  
  # DCA Intelligent
  dca_smart:
    enabled: false
    base_order: 100            # USDT
    safety_orders: 5
    scale_multiplier: 1.5
    rsi_levels: [29, 27.5, 26, 24, 22]
    price_drops: [0.015, 0.025, 0.04, 0.06, 0.10]

# ============================================================================
# ANALYSE ON-CHAIN
# ============================================================================
onchain:
  enabled: false               # Activer si API keys disponibles
  
  # Seuils MVRV
  mvrv:
    extreme_euphoria: 3.5      # VENDRE - distribution probable
    overheated: 2.4            # Prendre profits partiels
    equilibrium: 1.0           # Neutre
    undervalued: 0.8           # ACHETER FORT - capitulation
  
  # Seuils NUPL
  nupl:
    euphoria: 0.75             # VENDRE
    strong_conviction: 0.50    # Réduire exposition
    capitulation: 0.0          # ACHETER
  
  # Funding Rates
  funding:
    extreme_long: 0.001        # > 0.1% (8h) = correction probable
    caution: 0.0005            # Prudence sur nouveaux longs
    short_squeeze: 0.0         # < 0 = setup long squeeze
  
  # Whale Thresholds
  whale:
    btc_threshold: 100         # Transactions > 100 BTC
    eth_threshold: 1000        # Transactions > 1000 ETH
    usd_threshold: 500000      # Transactions > $500K

# ============================================================================
# DÉTECTION DE MANIPULATION
# ============================================================================
manipulation:
  # Order Book Imbalance
  obi:
    bullish_threshold: 0.3     # OBI > 0.3 = pression acheteuse
    bearish_threshold: -0.3    # OBI < -0.3 = pression vendeuse
  
  # Seuils de sécurité
  safety:
    max_spread_percent: 0.002  # Spread max 0.2%
    max_vol_depth_ratio: 30    # Éviter si > 50
    max_cancel_rate: 0.6       # Éviter si > 80%
  
  # Spoofing detection
  spoofing:
    order_lifetime_seconds: 1  # Ordre annulé < 1s
    cancel_rate_threshold: 0.8 # > 80% = spoofing probable

# ============================================================================
# COÛTS ET FRAIS
# ============================================================================
costs:
  commission_percent: 0.001    # 0.1% par trade (maker/taker moyen)
  min_profit_threshold: 0.005  # 0.5% minimum pour être rentable
  
  # Slippage estimé
  slippage:
    liquid_majors: 0.0001      # 0.01% BTC/ETH
    volatile: 0.0005           # 0.05% haute volatilité
    altcoins: 0.005            # 0.5% altcoins

# ============================================================================
# VÉRIFICATIONS PRÉ-TRADE
# ============================================================================
pre_trade_checks:
  - "daily_loss < MAX_DAILY_DRAWDOWN"
  - "consecutive_losses < 3"
  - "total_exposure < 6%"
  - "spread < 0.2%"
  - "sufficient_liquidity"
  - "not_in_pause_period"

# ============================================================================
# API SERVER
# ============================================================================
api:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:5173"
    - "http://localhost:3000"

# Mise à jour des données
data:
  update_interval: 5           # Secondes entre chaque update
  history_bars: 500

# Database
database:
  path: "data/trades.db"
```

---

## 🔧 Code Backend Python

### backend/config.py

```python
"""
Configuration loader for the trading bot.
Charge la configuration depuis le fichier YAML et les variables d'environnement.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing all configuration
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    if os.getenv('EXCHANGE'):
        config['exchange']['name'] = os.getenv('EXCHANGE')
    if os.getenv('TESTNET'):
        config['exchange']['testnet'] = os.getenv('TESTNET').lower() == 'true'
    if os.getenv('INITIAL_CAPITAL'):
        config['paper_trading']['initial_capital'] = float(os.getenv('INITIAL_CAPITAL'))
    if os.getenv('DATABASE_URL'):
        config['database']['url'] = os.getenv('DATABASE_URL')
    
    # On-chain API keys
    if os.getenv('GLASSNODE_API_KEY'):
        config['onchain']['glassnode_api_key'] = os.getenv('GLASSNODE_API_KEY')
        config['onchain']['enabled'] = True
    if os.getenv('COINGLASS_API_KEY'):
        config['onchain']['coinglass_api_key'] = os.getenv('COINGLASS_API_KEY')
    
    return config


# Global config instance
CONFIG = load_config()
```

### backend/data/fetcher.py

```python
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
        self.exchange_id = config['exchange']['name']
        self.symbols = config['symbols']
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.exchange = self._init_exchange()
        
    def _init_exchange(self):
        """Initialise la connexion à l'exchange."""
        exchange_class = getattr(ccxt, self.exchange_id)
        exchange = exchange_class({
            'enableRateLimit': self.config['exchange'].get('rate_limit', True),
            'options': {'defaultType': 'spot'}
        })
        
        if self.config['exchange'].get('testnet', True):
            if hasattr(exchange, 'set_sandbox_mode'):
                exchange.set_sandbox_mode(True)
                logger.info(f"Mode testnet activé pour {self.exchange_id}")
        
        return exchange
    
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
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'volume_24h': ticker['baseVolume'],
                'change_24h': ticker['percentage'],
                'spread': (ticker['ask'] - ticker['bid']) / ticker['last'] if ticker['last'] else 0,
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
    
    def get_cached_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Récupère les données en cache."""
        cache_key = f"{symbol}_{timeframe}"
        return self.data_cache.get(cache_key)
```

### backend/indicators/technical.py

```python
"""
Module de calcul des indicateurs techniques.

Indicateurs implémentés (selon TRADING_STRATEGIES_GUIDE.md):
- RSI (Relative Strength Index) - période 14, seuils 30/70 ou 20/80 crypto
- MACD (Moving Average Convergence Divergence) - 12/26/9
- Bollinger Bands - période 20, 2.0 écarts-types
- ATR (Average True Range) - période 14
- EMA/SMA (Moyennes Mobiles) - 9, 21, 50, 200
- ADX (Average Directional Index) - période 14, seuil 25
- Stochastic Oscillator
"""

import pandas as pd
import numpy as np
from typing import Dict
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, ADXIndicator, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Calcule tous les indicateurs techniques.
    
    Paramètres optimisés selon le Guide de Stratégies pour le trading crypto.
    """
    
    def __init__(self, config: dict):
        """
        Initialise les indicateurs avec la configuration.
        
        Args:
            config: Configuration complète du bot
        """
        self.config = config.get('indicators', {})
        
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule tous les indicateurs sur un DataFrame.
        
        Args:
            df: DataFrame avec colonnes OHLCV (open, high, low, close, volume)
            
        Returns:
            DataFrame enrichi avec tous les indicateurs
        """
        df = df.copy()
        df = self.add_rsi(df)
        df = self.add_macd(df)
        df = self.add_bollinger_bands(df)
        df = self.add_atr(df)
        df = self.add_emas(df)
        df = self.add_adx(df)
        df = self.add_stochastic(df)
        df = self.add_trend_filter(df)
        return df
    
    def add_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le RSI (Relative Strength Index).
        
        Formule: RSI = 100 - (100 / (1 + RS))
        où RS = Moyenne des gains / Moyenne des pertes sur n périodes
        
        Seuils standard: 30/70
        Seuils crypto volatile: 20/80
        """
        period = self.config.get('rsi', {}).get('period', 14)
        rsi = RSIIndicator(close=df['close'], window=period)
        df['rsi'] = rsi.rsi()
        return df
    
    def add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le MACD (Moving Average Convergence Divergence).
        
        Paramètres standard: EMA 12, EMA 26, Signal 9
        Signal d'achat: MACD croise au-dessus du Signal (surtout sous zéro)
        Signal de vente: MACD croise en dessous du Signal
        """
        macd_config = self.config.get('macd', {})
        macd = MACD(
            close=df['close'],
            window_fast=macd_config.get('fast', 12),
            window_slow=macd_config.get('slow', 26),
            window_sign=macd_config.get('signal', 9)
        )
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()
        return df
    
    def add_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute les Bollinger Bands.
        
        Paramètres: période 20-21, 2.0 écarts-types
        Squeeze detection: BBW < SMA(BBW, 50) × 0.75 = breakout imminent
        """
        bb_config = self.config.get('bollinger', {})
        bb = BollingerBands(
            close=df['close'],
            window=bb_config.get('period', 20),
            window_dev=bb_config.get('std_dev', 2)
        )
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_width'] = bb.bollinger_wband()
        df['bb_percent'] = bb.bollinger_pband()
        
        # Détection de squeeze
        squeeze_threshold = bb_config.get('squeeze_threshold', 0.75)
        bb_width_sma = df['bb_width'].rolling(50).mean()
        df['bb_squeeze'] = df['bb_width'] < (bb_width_sma * squeeze_threshold)
        
        return df
    
    def add_atr(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute l'ATR (Average True Range).
        
        Période: 14
        Utilisation: Stop = Entry ± (ATR × multiplicateur)
        Multiplicateurs: Day trading 1.5-2.0, Swing 2.0-2.5, Volatile 3.0-4.0
        """
        period = self.config.get('atr', {}).get('period', 14)
        atr = AverageTrueRange(
            high=df['high'], low=df['low'], close=df['close'], window=period
        )
        df['atr'] = atr.average_true_range()
        df['atr_percent'] = df['atr'] / df['close'] * 100
        return df
    
    def add_emas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute les EMAs (Exponential Moving Averages).
        
        - EMA 9: momentum court terme, scalping
        - EMA 21: tendance court terme, day trading
        - EMA 50: tendance moyen terme
        - SMA 200: tendance long terme, support/résistance majeur
        """
        ema_config = self.config.get('ema', {})
        
        df['ema_9'] = EMAIndicator(
            close=df['close'], window=ema_config.get('fast', 9)
        ).ema_indicator()
        
        df['ema_21'] = EMAIndicator(
            close=df['close'], window=ema_config.get('slow', 21)
        ).ema_indicator()
        
        df['ema_50'] = EMAIndicator(
            close=df['close'], window=ema_config.get('trend', 50)
        ).ema_indicator()
        
        df['sma_200'] = SMAIndicator(
            close=df['close'], window=200
        ).sma_indicator()
        
        # Aliases pour compatibilité
        df['ema_fast'] = df['ema_9']
        df['ema_slow'] = df['ema_21']
        df['ema_trend'] = df['ema_50']
        
        return df
    
    def add_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute l'ADX (Average Directional Index).
        
        Période: 14
        Seuil: ADX > 25 = marché en tendance
        ADX < 20 = marché ranging/consolidation
        """
        adx = ADXIndicator(
            high=df['high'], low=df['low'], close=df['close'], window=14
        )
        df['adx'] = adx.adx()
        df['adx_pos'] = adx.adx_pos()  # +DI
        df['adx_neg'] = adx.adx_neg()  # -DI
        
        # Flag pour marché en tendance
        adx_threshold = self.config.get('adx', {}).get('threshold', 25)
        df['trending'] = df['adx'] > adx_threshold
        
        return df
    
    def add_stochastic(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le Stochastic Oscillator.
        
        Paramètres: K=14, D=3
        Suracheté: > 80
        Survendu: < 20
        """
        stoch_config = self.config.get('stochastic', {})
        stoch = StochasticOscillator(
            high=df['high'], 
            low=df['low'], 
            close=df['close'], 
            window=stoch_config.get('k_period', 14),
            smooth_window=stoch_config.get('d_period', 3)
        )
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        return df
    
    def add_trend_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute un filtre de tendance basé sur la SMA 200.
        
        Règle: price > SMA 200 = tendance haussière (favoriser les longs)
        """
        if 'sma_200' in df.columns:
            df['above_sma200'] = df['close'] > df['sma_200']
            df['trend_bias'] = np.where(df['above_sma200'], 1, -1)
        return df
    
    def get_current_values(self, df: pd.DataFrame) -> Dict:
        """
        Récupère les valeurs actuelles de tous les indicateurs.
        
        Args:
            df: DataFrame avec indicateurs calculés
            
        Returns:
            Dict avec les valeurs actuelles
        """
        if df.empty:
            return {}
        
        last = df.iloc[-1]
        return {
            'rsi': round(last.get('rsi', 0), 2) if pd.notna(last.get('rsi')) else None,
            'macd': round(last.get('macd', 0), 4) if pd.notna(last.get('macd')) else None,
            'macd_signal': round(last.get('macd_signal', 0), 4) if pd.notna(last.get('macd_signal')) else None,
            'macd_histogram': round(last.get('macd_histogram', 0), 4) if pd.notna(last.get('macd_histogram')) else None,
            'bb_upper': round(last.get('bb_upper', 0), 2) if pd.notna(last.get('bb_upper')) else None,
            'bb_middle': round(last.get('bb_middle', 0), 2) if pd.notna(last.get('bb_middle')) else None,
            'bb_lower': round(last.get('bb_lower', 0), 2) if pd.notna(last.get('bb_lower')) else None,
            'bb_squeeze': bool(last.get('bb_squeeze', False)),
            'atr': round(last.get('atr', 0), 2) if pd.notna(last.get('atr')) else None,
            'atr_percent': round(last.get('atr_percent', 0), 4) if pd.notna(last.get('atr_percent')) else None,
            'adx': round(last.get('adx', 0), 2) if pd.notna(last.get('adx')) else None,
            'trending': bool(last.get('trending', False)),
            'stoch_k': round(last.get('stoch_k', 0), 2) if pd.notna(last.get('stoch_k')) else None,
            'stoch_d': round(last.get('stoch_d', 0), 2) if pd.notna(last.get('stoch_d')) else None,
            'ema_9': round(last.get('ema_9', 0), 2) if pd.notna(last.get('ema_9')) else None,
            'ema_21': round(last.get('ema_21', 0), 2) if pd.notna(last.get('ema_21')) else None,
            'ema_50': round(last.get('ema_50', 0), 2) if pd.notna(last.get('ema_50')) else None,
            'sma_200': round(last.get('sma_200', 0), 2) if pd.notna(last.get('sma_200')) else None,
            'trend_bias': int(last.get('trend_bias', 0)) if pd.notna(last.get('trend_bias')) else 0,
            'close': round(last.get('close', 0), 2) if pd.notna(last.get('close')) else None,
            'volume': round(last.get('volume', 0), 2) if pd.notna(last.get('volume')) else None
        }
```

### backend/indicators/patterns.py

```python
"""
Module de détection des patterns de chandeliers japonais.

Patterns implémentés (selon TRADING_STRATEGIES_GUIDE.md):
- Hammer (fiabilité 8/10)
- Engulfing (fiabilité 9/10)
- Morning/Evening Star (fiabilité 9/10)
- Doji
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CandlePattern:
    """Pattern de chandelier détecté."""
    name: str
    type: str  # 'bullish' ou 'bearish'
    index: int
    confidence: float  # 0.0 à 1.0
    description: str


class PatternDetector:
    """
    Détecte les patterns de chandeliers japonais.
    
    Critères de validation stricts selon le Guide de Stratégies.
    """
    
    def __init__(self, config: dict):
        """
        Initialise le détecteur avec la configuration.
        
        Args:
            config: Configuration contenant les paramètres des patterns
        """
        self.config = config.get('patterns', {})
        
    def detect_all(self, df: pd.DataFrame) -> List[CandlePattern]:
        """
        Détecte tous les patterns sur les dernières bougies.
        
        Args:
            df: DataFrame OHLCV
            
        Returns:
            Liste des patterns détectés
        """
        patterns = []
        
        # Détection sur les 3 dernières bougies
        if len(df) >= 3:
            hammer = self.detect_hammer(df)
            if hammer:
                patterns.append(hammer)
            
            engulfing = self.detect_engulfing(df)
            if engulfing:
                patterns.append(engulfing)
            
            star = self.detect_star(df)
            if star:
                patterns.append(star)
            
            doji = self.detect_doji(df)
            if doji:
                patterns.append(doji)
        
        return patterns
    
    def detect_hammer(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte un Hammer (marteau).
        
        Critères (fiabilité 8/10):
        - Mèche inférieure ≥ 2× corps
        - Mèche supérieure ≤ 10% du range
        - Doit apparaître en bas de tendance baissière
        
        Formule: (open - low) >= 2 × |open - close| 
                 AND (high - max(open,close)) <= 0.1 × (high - low)
        """
        if len(df) < 10:
            return None
        
        config = self.config.get('hammer', {})
        last = df.iloc[-1]
        
        body = abs(last['close'] - last['open'])
        total_range = last['high'] - last['low']
        
        if total_range == 0:
            return None
        
        lower_wick = min(last['open'], last['close']) - last['low']
        upper_wick = last['high'] - max(last['open'], last['close'])
        
        lower_wick_ratio = config.get('lower_wick_ratio', 2.0)
        upper_wick_max = config.get('upper_wick_max', 0.1)
        
        # Vérification des critères
        if lower_wick >= (lower_wick_ratio * body) and upper_wick <= (upper_wick_max * total_range):
            # Vérifier tendance baissière précédente
            prev_closes = df['close'].iloc[-10:-1]
            if prev_closes.iloc[-1] < prev_closes.iloc[0]:
                return CandlePattern(
                    name="Hammer",
                    type="bullish",
                    index=len(df) - 1,
                    confidence=0.8,
                    description="Marteau détecté en bas de tendance - signal de retournement haussier"
                )
        
        return None
    
    def detect_engulfing(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte un Engulfing (engloutissante).
        
        Critères (fiabilité 9/10):
        - Le corps de la bougie actuelle englobe entièrement le corps précédent
        - Bullish: current_close > prev_open AND current_open < prev_close
        - Bearish: current_close < prev_open AND current_open > prev_close
        """
        if len(df) < 2:
            return None
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        current_body = abs(current['close'] - current['open'])
        prev_body = abs(prev['close'] - prev['open'])
        
        config = self.config.get('engulfing', {})
        min_body_ratio = config.get('min_body_ratio', 0.6)
        
        # Corps significatif requis
        current_range = current['high'] - current['low']
        if current_range == 0 or (current_body / current_range) < min_body_ratio:
            return None
        
        # Bullish Engulfing
        if (current['close'] > current['open'] and  # Bougie verte
            prev['close'] < prev['open'] and  # Bougie rouge précédente
            current['close'] > prev['open'] and
            current['open'] < prev['close']):
            return CandlePattern(
                name="Bullish Engulfing",
                type="bullish",
                index=len(df) - 1,
                confidence=0.9,
                description="Engloutissante haussière - fort signal d'achat"
            )
        
        # Bearish Engulfing
        if (current['close'] < current['open'] and  # Bougie rouge
            prev['close'] > prev['open'] and  # Bougie verte précédente
            current['close'] < prev['open'] and
            current['open'] > prev['close']):
            return CandlePattern(
                name="Bearish Engulfing",
                type="bearish",
                index=len(df) - 1,
                confidence=0.9,
                description="Engloutissante baissière - fort signal de vente"
            )
        
        return None
    
    def detect_star(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte Morning Star / Evening Star.
        
        Critères (fiabilité 9/10):
        - Pattern à 3 bougies
        - Bougie centrale = petit corps (doji-like)
        - 3ème bougie clôture au-delà du point médian de la 1ère
        """
        if len(df) < 3:
            return None
        
        first = df.iloc[-3]
        middle = df.iloc[-2]
        last = df.iloc[-1]
        
        first_body = abs(first['close'] - first['open'])
        middle_body = abs(middle['close'] - middle['open'])
        last_body = abs(last['close'] - last['open'])
        
        first_range = first['high'] - first['low']
        middle_range = middle['high'] - middle['low']
        
        if first_range == 0 or middle_range == 0:
            return None
        
        # Bougie centrale doit être petite (< 30% du range)
        if (middle_body / middle_range) > 0.3:
            return None
        
        first_midpoint = (first['open'] + first['close']) / 2
        
        # Morning Star (bullish)
        if (first['close'] < first['open'] and  # 1ère rouge
            last['close'] > last['open'] and  # 3ème verte
            last['close'] > first_midpoint):  # Clôture au-dessus du milieu
            return CandlePattern(
                name="Morning Star",
                type="bullish",
                index=len(df) - 1,
                confidence=0.9,
                description="Étoile du matin - signal de retournement haussier fort"
            )
        
        # Evening Star (bearish)
        if (first['close'] > first['open'] and  # 1ère verte
            last['close'] < last['open'] and  # 3ème rouge
            last['close'] < first_midpoint):  # Clôture en dessous du milieu
            return CandlePattern(
                name="Evening Star",
                type="bearish",
                index=len(df) - 1,
                confidence=0.9,
                description="Étoile du soir - signal de retournement baissier fort"
            )
        
        return None
    
    def detect_doji(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte un Doji.
        
        Critères:
        - Corps très petit (≤ 5% du range)
        - Indécision du marché
        """
        if len(df) < 1:
            return None
        
        config = self.config.get('doji', {})
        last = df.iloc[-1]
        
        body = abs(last['close'] - last['open'])
        total_range = last['high'] - last['low']
        
        if total_range == 0:
            return None
        
        body_max_ratio = config.get('body_max_ratio', 0.05)
        
        if (body / total_range) <= body_max_ratio:
            return CandlePattern(
                name="Doji",
                type="neutral",
                index=len(df) - 1,
                confidence=0.6,
                description="Doji - indécision du marché, attendre confirmation"
            )
        
        return None
    
    def add_pattern_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute des colonnes de patterns au DataFrame.
        
        Args:
            df: DataFrame OHLCV
            
        Returns:
            DataFrame avec colonnes pattern_*
        """
        df = df.copy()
        df['pattern_bullish'] = False
        df['pattern_bearish'] = False
        df['pattern_name'] = ''
        
        for i in range(3, len(df)):
            subset = df.iloc[:i+1].copy()
            patterns = self.detect_all(subset)
            
            for pattern in patterns:
                if pattern.type == 'bullish':
                    df.iloc[i, df.columns.get_loc('pattern_bullish')] = True
                elif pattern.type == 'bearish':
                    df.iloc[i, df.columns.get_loc('pattern_bearish')] = True
                df.iloc[i, df.columns.get_loc('pattern_name')] = pattern.name
        
        return df
```

### backend/indicators/divergences.py

```python
"""
Module de détection des divergences RSI/MACD.

Types de divergences (selon TRADING_STRATEGIES_GUIDE.md):
- Divergence régulière baissière: prix HH, indicateur LH → retournement
- Divergence régulière haussière: prix LL, indicateur HL → retournement
- Divergence cachée haussière: prix HL, indicateur LL → continuation
- Divergence cachée baissière: prix LH, indicateur HH → continuation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Divergence:
    """Divergence détectée."""
    type: str  # 'regular_bullish', 'regular_bearish', 'hidden_bullish', 'hidden_bearish'
    indicator: str  # 'rsi' ou 'macd'
    start_index: int
    end_index: int
    confidence: float
    description: str


class DivergenceDetector:
    """
    Détecte les divergences entre prix et indicateurs.
    
    Les divergences sont des signaux puissants de retournement ou continuation.
    """
    
    def __init__(self, config: dict):
        """
        Initialise le détecteur.
        
        Args:
            config: Configuration du bot
        """
        self.config = config
        self.lookback = 20  # Nombre de bougies pour chercher les divergences
        
    def detect_all(self, df: pd.DataFrame) -> List[Divergence]:
        """
        Détecte toutes les divergences RSI et MACD.
        
        Args:
            df: DataFrame avec RSI et MACD calculés
            
        Returns:
            Liste des divergences détectées
        """
        divergences = []
        
        if 'rsi' in df.columns:
            rsi_divs = self._detect_indicator_divergences(df, 'rsi')
            divergences.extend(rsi_divs)
        
        if 'macd' in df.columns:
            macd_divs = self._detect_indicator_divergences(df, 'macd')
            divergences.extend(macd_divs)
        
        return divergences
    
    def _detect_indicator_divergences(
        self, 
        df: pd.DataFrame, 
        indicator: str
    ) -> List[Divergence]:
        """
        Détecte les divergences pour un indicateur spécifique.
        
        Args:
            df: DataFrame avec indicateur
            indicator: Nom de la colonne indicateur
            
        Returns:
            Liste des divergences
        """
        divergences = []
        
        if len(df) < self.lookback:
            return divergences
        
        # Trouver les pivots (highs et lows locaux)
        price_highs, price_lows = self._find_pivots(df['close'], 5)
        ind_highs, ind_lows = self._find_pivots(df[indicator], 5)
        
        # Chercher divergences dans la fenêtre récente
        recent_df = df.iloc[-self.lookback:]
        
        # Divergence régulière baissière: prix HH, indicateur LH
        regular_bearish = self._check_regular_bearish(
            recent_df, indicator, price_highs, ind_highs
        )
        if regular_bearish:
            divergences.append(regular_bearish)
        
        # Divergence régulière haussière: prix LL, indicateur HL
        regular_bullish = self._check_regular_bullish(
            recent_df, indicator, price_lows, ind_lows
        )
        if regular_bullish:
            divergences.append(regular_bullish)
        
        # Divergence cachée haussière: prix HL, indicateur LL
        hidden_bullish = self._check_hidden_bullish(
            recent_df, indicator, price_lows, ind_lows
        )
        if hidden_bullish:
            divergences.append(hidden_bullish)
        
        # Divergence cachée baissière: prix LH, indicateur HH
        hidden_bearish = self._check_hidden_bearish(
            recent_df, indicator, price_highs, ind_highs
        )
        if hidden_bearish:
            divergences.append(hidden_bearish)
        
        return divergences
    
    def _find_pivots(
        self, 
        series: pd.Series, 
        window: int = 5
    ) -> Tuple[List[int], List[int]]:
        """
        Trouve les pivots hauts et bas dans une série.
        
        Args:
            series: Série de données
            window: Fenêtre pour détection des pivots
            
        Returns:
            Tuple (indices des highs, indices des lows)
        """
        highs = []
        lows = []
        
        for i in range(window, len(series) - window):
            window_data = series.iloc[i-window:i+window+1]
            
            if series.iloc[i] == window_data.max():
                highs.append(i)
            if series.iloc[i] == window_data.min():
                lows.append(i)
        
        return highs, lows
    
    def _check_regular_bearish(
        self, 
        df: pd.DataFrame, 
        indicator: str,
        price_highs: List[int],
        ind_highs: List[int]
    ) -> Optional[Divergence]:
        """
        Vérifie divergence régulière baissière.
        Prix fait des higher highs, indicateur fait des lower highs.
        """
        if len(price_highs) < 2 or len(ind_highs) < 2:
            return None
        
        # Derniers deux highs
        ph1, ph2 = price_highs[-2], price_highs[-1]
        
        # Vérifier si le prix fait des HH
        if df['close'].iloc[ph2] <= df['close'].iloc[ph1]:
            return None
        
        # Trouver les highs indicateur correspondants
        ih1 = self._find_nearest_pivot(ind_highs, ph1)
        ih2 = self._find_nearest_pivot(ind_highs, ph2)
        
        if ih1 is None or ih2 is None:
            return None
        
        # Vérifier si l'indicateur fait des LH
        if df[indicator].iloc[ih2] < df[indicator].iloc[ih1]:
            return Divergence(
                type='regular_bearish',
                indicator=indicator,
                start_index=ph1,
                end_index=ph2,
                confidence=0.85,
                description=f"Divergence baissière {indicator.upper()}: prix HH, {indicator.upper()} LH - retournement probable"
            )
        
        return None
    
    def _check_regular_bullish(
        self, 
        df: pd.DataFrame, 
        indicator: str,
        price_lows: List[int],
        ind_lows: List[int]
    ) -> Optional[Divergence]:
        """
        Vérifie divergence régulière haussière.
        Prix fait des lower lows, indicateur fait des higher lows.
        """
        if len(price_lows) < 2 or len(ind_lows) < 2:
            return None
        
        pl1, pl2 = price_lows[-2], price_lows[-1]
        
        if df['close'].iloc[pl2] >= df['close'].iloc[pl1]:
            return None
        
        il1 = self._find_nearest_pivot(ind_lows, pl1)
        il2 = self._find_nearest_pivot(ind_lows, pl2)
        
        if il1 is None or il2 is None:
            return None
        
        if df[indicator].iloc[il2] > df[indicator].iloc[il1]:
            return Divergence(
                type='regular_bullish',
                indicator=indicator,
                start_index=pl1,
                end_index=pl2,
                confidence=0.85,
                description=f"Divergence haussière {indicator.upper()}: prix LL, {indicator.upper()} HL - retournement probable"
            )
        
        return None
    
    def _check_hidden_bullish(
        self, 
        df: pd.DataFrame, 
        indicator: str,
        price_lows: List[int],
        ind_lows: List[int]
    ) -> Optional[Divergence]:
        """
        Vérifie divergence cachée haussière.
        Prix fait des higher lows, indicateur fait des lower lows.
        Signal de continuation de tendance haussière.
        """
        if len(price_lows) < 2 or len(ind_lows) < 2:
            return None
        
        pl1, pl2 = price_lows[-2], price_lows[-1]
        
        if df['close'].iloc[pl2] <= df['close'].iloc[pl1]:
            return None
        
        il1 = self._find_nearest_pivot(ind_lows, pl1)
        il2 = self._find_nearest_pivot(ind_lows, pl2)
        
        if il1 is None or il2 is None:
            return None
        
        if df[indicator].iloc[il2] < df[indicator].iloc[il1]:
            return Divergence(
                type='hidden_bullish',
                indicator=indicator,
                start_index=pl1,
                end_index=pl2,
                confidence=0.75,
                description=f"Divergence cachée haussière {indicator.upper()}: continuation de tendance haussière"
            )
        
        return None
    
    def _check_hidden_bearish(
        self, 
        df: pd.DataFrame, 
        indicator: str,
        price_highs: List[int],
        ind_highs: List[int]
    ) -> Optional[Divergence]:
        """
        Vérifie divergence cachée baissière.
        Prix fait des lower highs, indicateur fait des higher highs.
        Signal de continuation de tendance baissière.
        """
        if len(price_highs) < 2 or len(ind_highs) < 2:
            return None
        
        ph1, ph2 = price_highs[-2], price_highs[-1]
        
        if df['close'].iloc[ph2] >= df['close'].iloc[ph1]:
            return None
        
        ih1 = self._find_nearest_pivot(ind_highs, ph1)
        ih2 = self._find_nearest_pivot(ind_highs, ph2)
        
        if ih1 is None or ih2 is None:
            return None
        
        if df[indicator].iloc[ih2] > df[indicator].iloc[ih1]:
            return Divergence(
                type='hidden_bearish',
                indicator=indicator,
                start_index=ph1,
                end_index=ph2,
                confidence=0.75,
                description=f"Divergence cachée baissière {indicator.upper()}: continuation de tendance baissière"
            )
        
        return None
    
    def _find_nearest_pivot(
        self, 
        pivots: List[int], 
        target: int, 
        max_distance: int = 3
    ) -> Optional[int]:
        """Trouve le pivot le plus proche d'un index cible."""
        if not pivots:
            return None
        
        nearest = min(pivots, key=lambda x: abs(x - target))
        if abs(nearest - target) <= max_distance:
            return nearest
        return None
```

### backend/indicators/smc.py

```python
"""
Module Smart Money Concepts (SMC/ICT).

Implémente (selon TRADING_STRATEGIES_GUIDE.md):
- Swing Highs/Lows
- Order Blocks (OB)
- Fair Value Gaps (FVG)
- Break of Structure (BOS)
- Change of Character (CHoCH)
- Market Bias
- Kill Zones
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)


@dataclass
class SwingPoint:
    """Point de swing (high ou low)."""
    index: int
    price: float
    timestamp: pd.Timestamp
    type: str  # 'high' ou 'low'


@dataclass
class OrderBlock:
    """
    Zone d'Order Block.
    
    Bullish OB: dernière bougie baissière avant un mouvement haussier fort
    Bearish OB: dernière bougie haussière avant un mouvement baissier fort
    """
    index: int
    top: float
    bottom: float
    type: str  # 'bullish' ou 'bearish'
    volume: float
    mitigated: bool = False


@dataclass
class FairValueGap:
    """
    Fair Value Gap (FVG).
    
    Pattern à 3 bougies où le corps/mèche de la bougie centrale 
    ne touche pas les mèches des bougies environnantes.
    """
    index: int
    top: float
    bottom: float
    type: str  # 'bullish' ou 'bearish'
    midpoint: float  # Consequent Encroachment point
    filled: bool = False


@dataclass
class StructureBreak:
    """
    Break of Structure (BOS) ou Change of Character (CHoCH).
    
    BOS: cassure du swing précédent dans la direction de la tendance
    CHoCH: première cassure contre la tendance actuelle
    """
    index: int
    price: float
    type: str  # 'bos_bullish', 'bos_bearish', 'choch_bullish', 'choch_bearish'
    swing_broken: SwingPoint


class SmartMoneyConcepts:
    """
    Analyse Smart Money Concepts (ICT).
    
    Identifie les "empreintes" institutionnelles dans le prix.
    """
    
    def __init__(self, config: dict):
        """
        Initialise l'analyse SMC.
        
        Args:
            config: Configuration contenant les paramètres SMC
        """
        self.config = config.get('smc', {})
        self.swing_length = self.config.get('swing_length', 10)
        self.fvg_min_size = self.config.get('fvg_min_size', 0.001)
        self.ob_volume_threshold = self.config.get('ob_volume_threshold', 1.5)
        self.displacement_atr = self.config.get('displacement_atr', 2.0)
        
        # Kill Zones (EST)
        self.kill_zones = self.config.get('kill_zones', {
            'london_open': '02:00',
            'london_close': '05:00',
            'ny_open': '07:00',
            'ny_close': '10:00',
            'silver_bullet': '10:00',
            'silver_bullet_end': '11:00'
        })
        
        # Structures détectées
        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []
        self.order_blocks: List[OrderBlock] = []
        self.fvgs: List[FairValueGap] = []
        self.structure_breaks: List[StructureBreak] = []
        
    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Effectue l'analyse SMC complète.
        
        Args:
            df: DataFrame avec données OHLCV et ATR
            
        Returns:
            DataFrame enrichi avec colonnes SMC
        """
        df = df.copy()
        df = self._identify_swing_points(df)
        df = self._identify_fvg(df)
        df = self._identify_order_blocks(df)
        df = self._identify_structure_breaks(df)
        df['market_bias'] = self._calculate_market_bias(df)
        df = self._add_kill_zones(df)
        return df
    
    def _identify_swing_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identifie les swing highs et lows."""
        df['swing_high'] = 0.0
        df['swing_low'] = 0.0
        self.swing_highs = []
        self.swing_lows = []
        
        for i in range(self.swing_length, len(df) - self.swing_length):
            # Swing high
            window_high = df['high'].iloc[i-self.swing_length:i+self.swing_length+1].max()
            if df['high'].iloc[i] == window_high:
                df.iloc[i, df.columns.get_loc('swing_high')] = df['high'].iloc[i]
                self.swing_highs.append(SwingPoint(
                    i, df['high'].iloc[i], df.index[i], 'high'
                ))
            
            # Swing low
            window_low = df['low'].iloc[i-self.swing_length:i+self.swing_length+1].min()
            if df['low'].iloc[i] == window_low:
                df.iloc[i, df.columns.get_loc('swing_low')] = df['low'].iloc[i]
                self.swing_lows.append(SwingPoint(
                    i, df['low'].iloc[i], df.index[i], 'low'
                ))
        
        return df
    
    def _identify_fvg(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identifie les Fair Value Gaps.
        
        Bullish FVG: candle1.high < candle3.low (gap up)
        Bearish FVG: candle1.low > candle3.high (gap down)
        """
        df['fvg_bullish_top'] = np.nan
        df['fvg_bullish_bottom'] = np.nan
        df['fvg_bearish_top'] = np.nan
        df['fvg_bearish_bottom'] = np.nan
        self.fvgs = []
        
        for i in range(2, len(df)):
            # FVG Bullish (gap up)
            if df['low'].iloc[i] > df['high'].iloc[i-2]:
                gap_size = (df['low'].iloc[i] - df['high'].iloc[i-2]) / df['close'].iloc[i]
                if gap_size >= self.fvg_min_size:
                    top = df['low'].iloc[i]
                    bottom = df['high'].iloc[i-2]
                    df.iloc[i-1, df.columns.get_loc('fvg_bullish_top')] = top
                    df.iloc[i-1, df.columns.get_loc('fvg_bullish_bottom')] = bottom
                    self.fvgs.append(FairValueGap(
                        index=i-1,
                        top=top,
                        bottom=bottom,
                        type='bullish',
                        midpoint=(top + bottom) / 2
                    ))
            
            # FVG Bearish (gap down)
            if df['high'].iloc[i] < df['low'].iloc[i-2]:
                gap_size = (df['low'].iloc[i-2] - df['high'].iloc[i]) / df['close'].iloc[i]
                if gap_size >= self.fvg_min_size:
                    top = df['low'].iloc[i-2]
                    bottom = df['high'].iloc[i]
                    df.iloc[i-1, df.columns.get_loc('fvg_bearish_top')] = top
                    df.iloc[i-1, df.columns.get_loc('fvg_bearish_bottom')] = bottom
                    self.fvgs.append(FairValueGap(
                        index=i-1,
                        top=top,
                        bottom=bottom,
                        type='bearish',
                        midpoint=(top + bottom) / 2
                    ))
        
        return df
    
    def _identify_order_blocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identifie les Order Blocks.
        
        Critères:
        - Displacement = move > ATR × 2
        - Bullish OB: bearish candle BEFORE displacement_up
        - Bearish OB: bullish candle BEFORE displacement_down
        """
        df['ob_bullish_top'] = np.nan
        df['ob_bullish_bottom'] = np.nan
        df['ob_bearish_top'] = np.nan
        df['ob_bearish_bottom'] = np.nan
        self.order_blocks = []
        
        # Utiliser ATR si disponible, sinon calculer
        if 'atr' not in df.columns:
            from ta.volatility import AverageTrueRange
            atr = AverageTrueRange(df['high'], df['low'], df['close'], window=14)
            df['atr'] = atr.average_true_range()
        
        avg_volume = df['volume'].rolling(20).mean()
        
        for i in range(3, len(df) - 1):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            atr_value = df['atr'].iloc[i] if pd.notna(df['atr'].iloc[i]) else 0
            
            # Volume filter
            if current['volume'] < avg_volume.iloc[i] * self.ob_volume_threshold:
                continue
            
            # Calcul du displacement
            displacement_threshold = atr_value * self.displacement_atr
            
            # Bullish OB: bearish candle followed by bullish impulse
            if (current['close'] > current['open'] and 
                prev['close'] < prev['open']):
                move = current['close'] - prev['low']
                if move > displacement_threshold and displacement_threshold > 0:
                    df.iloc[i-1, df.columns.get_loc('ob_bullish_top')] = prev['open']
                    df.iloc[i-1, df.columns.get_loc('ob_bullish_bottom')] = prev['low']
                    self.order_blocks.append(OrderBlock(
                        i-1, prev['open'], prev['low'], 'bullish', prev['volume']
                    ))
            
            # Bearish OB: bullish candle followed by bearish impulse
            if (current['close'] < current['open'] and 
                prev['close'] > prev['open']):
                move = prev['high'] - current['close']
                if move > displacement_threshold and displacement_threshold > 0:
                    df.iloc[i-1, df.columns.get_loc('ob_bearish_top')] = prev['high']
                    df.iloc[i-1, df.columns.get_loc('ob_bearish_bottom')] = prev['open']
                    self.order_blocks.append(OrderBlock(
                        i-1, prev['high'], prev['open'], 'bearish', prev['volume']
                    ))
        
        return df
    
    def _identify_structure_breaks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identifie les Break of Structure (BOS) et Change of Character (CHoCH).
        
        BOS: cassure du swing précédent dans la direction de la tendance
        CHoCH: première cassure contre la tendance actuelle
        """
        df['bos_bullish'] = False
        df['bos_bearish'] = False
        df['choch_bullish'] = False
        df['choch_bearish'] = False
        self.structure_breaks = []
        
        if len(self.swing_highs) < 2 or len(self.swing_lows) < 2:
            return df
        
        current_trend = 0  # 0: neutral, 1: bullish, -1: bearish
        
        for i in range(20, len(df)):
            close = df['close'].iloc[i]
            
            # Chercher le dernier swing high/low avant cet index
            recent_highs = [sh for sh in self.swing_highs if sh.index < i]
            recent_lows = [sl for sl in self.swing_lows if sl.index < i]
            
            if not recent_highs or not recent_lows:
                continue
            
            last_high = recent_highs[-1]
            last_low = recent_lows[-1]
            
            # BOS Bullish: close > previous swing high (body close required)
            if close > last_high.price:
                if current_trend >= 0:
                    df.iloc[i, df.columns.get_loc('bos_bullish')] = True
                    self.structure_breaks.append(StructureBreak(
                        i, close, 'bos_bullish', last_high
                    ))
                else:
                    # C'était bearish, maintenant break à la hausse = CHoCH
                    df.iloc[i, df.columns.get_loc('choch_bullish')] = True
                    self.structure_breaks.append(StructureBreak(
                        i, close, 'choch_bullish', last_high
                    ))
                current_trend = 1
            
            # BOS Bearish: close < previous swing low
            elif close < last_low.price:
                if current_trend <= 0:
                    df.iloc[i, df.columns.get_loc('bos_bearish')] = True
                    self.structure_breaks.append(StructureBreak(
                        i, close, 'bos_bearish', last_low
                    ))
                else:
                    # C'était bullish, maintenant break à la baisse = CHoCH
                    df.iloc[i, df.columns.get_loc('choch_bearish')] = True
                    self.structure_breaks.append(StructureBreak(
                        i, close, 'choch_bearish', last_low
                    ))
                current_trend = -1
        
        return df
    
    def _calculate_market_bias(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcule le bias de marché basé sur la structure.
        
        Returns:
            Series avec 1 (bullish), -1 (bearish), ou 0 (neutral)
        """
        bias = pd.Series(0, index=df.index)
        
        if len(self.swing_highs) >= 2 and len(self.swing_lows) >= 2:
            last_highs = self.swing_highs[-2:]
            last_lows = self.swing_lows[-2:]
            
            # Higher highs and higher lows = bullish (uptrend)
            if (last_highs[-1].price > last_highs[-2].price and 
                last_lows[-1].price > last_lows[-2].price):
                bias.iloc[-1] = 1
            # Lower highs and lower lows = bearish (downtrend)
            elif (last_highs[-1].price < last_highs[-2].price and 
                  last_lows[-1].price < last_lows[-2].price):
                bias.iloc[-1] = -1
        
        return bias
    
    def _add_kill_zones(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute les colonnes de Kill Zones.
        
        Kill Zones ICT (heures optimales pour trader - EST):
        - London: 2:00-5:00 AM
        - New York: 7:00-10:00 AM
        - Silver Bullet: 10:00-11:00 AM
        """
        df['in_kill_zone'] = False
        df['kill_zone_name'] = ''
        
        if not isinstance(df.index, pd.DatetimeIndex):
            return df
        
        for idx in df.index:
            hour = idx.hour
            minute = idx.minute
            current_time = hour * 60 + minute
            
            # London Kill Zone: 2:00-5:00 AM EST
            london_start = 2 * 60
            london_end = 5 * 60
            
            # NY Kill Zone: 7:00-10:00 AM EST
            ny_start = 7 * 60
            ny_end = 10 * 60
            
            # Silver Bullet: 10:00-11:00 AM EST
            sb_start = 10 * 60
            sb_end = 11 * 60
            
            if london_start <= current_time < london_end:
                df.loc[idx, 'in_kill_zone'] = True
                df.loc[idx, 'kill_zone_name'] = 'London'
            elif ny_start <= current_time < ny_end:
                df.loc[idx, 'in_kill_zone'] = True
                df.loc[idx, 'kill_zone_name'] = 'New York'
            elif sb_start <= current_time < sb_end:
                df.loc[idx, 'in_kill_zone'] = True
                df.loc[idx, 'kill_zone_name'] = 'Silver Bullet'
        
        return df
    
    def get_active_zones(self, current_price: float) -> Dict:
        """
        Récupère les zones SMC actives proches du prix actuel.
        
        Args:
            current_price: Prix actuel
            
        Returns:
            Dict avec les OB et FVG actifs
        """
        proximity = 0.02  # 2% du prix
        
        active_obs = [
            {
                'type': ob.type, 
                'top': ob.top, 
                'bottom': ob.bottom,
                'entry_zone': (ob.top + ob.bottom) / 2
            }
            for ob in self.order_blocks 
            if not ob.mitigated and 
               abs(current_price - (ob.top + ob.bottom) / 2) / current_price < proximity
        ]
        
        active_fvgs = [
            {
                'type': fvg.type, 
                'top': fvg.top, 
                'bottom': fvg.bottom,
                'midpoint': fvg.midpoint  # Point d'entrée CE
            }
            for fvg in self.fvgs 
            if not fvg.filled and
               abs(current_price - fvg.midpoint) / current_price < proximity
        ]
        
        return {
            'order_blocks': active_obs,
            'fair_value_gaps': active_fvgs
        }
    
    def get_structure_summary(self) -> Dict:
        """
        Retourne un résumé de la structure de marché.
        
        Returns:
            Dict avec le résumé SMC
        """
        return {
            'swing_highs_count': len(self.swing_highs),
            'swing_lows_count': len(self.swing_lows),
            'active_bullish_ob': len([ob for ob in self.order_blocks if ob.type == 'bullish' and not ob.mitigated]),
            'active_bearish_ob': len([ob for ob in self.order_blocks if ob.type == 'bearish' and not ob.mitigated]),
            'active_bullish_fvg': len([fvg for fvg in self.fvgs if fvg.type == 'bullish' and not fvg.filled]),
            'active_bearish_fvg': len([fvg for fvg in self.fvgs if fvg.type == 'bearish' and not fvg.filled]),
            'recent_bos': len([sb for sb in self.structure_breaks if 'bos' in sb.type]),
            'recent_choch': len([sb for sb in self.structure_breaks if 'choch' in sb.type])
        }
```

### backend/trading/risk_manager.py

```python
"""
Module de gestion des risques.

Implémente (selon TRADING_STRATEGIES_GUIDE.md):
- Position sizing (pourcentage fixe, Kelly Criterion, ATR-based)
- Stop-loss et take-profit
- Drawdown management
- Vérifications pré-trade
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class PositionSize:
    """Résultat du calcul de position sizing."""
    size: float              # Taille de la position en base currency
    size_quote: float        # Taille en quote currency
    risk_amount: float       # Montant risqué
    risk_percent: float      # Pourcentage du capital risqué
    kelly_full: float        # Kelly complet (pour info)
    kelly_used: float        # Kelly utilisé (quarter-kelly)


@dataclass
class StopTakeProfit:
    """Niveaux de stop-loss et take-profit."""
    stop_loss: float
    take_profit: float
    stop_distance: float
    take_distance: float
    risk_reward: float
    trailing_stop: Optional[float] = None


class RiskManager:
    """
    Gère tous les aspects du risque de trading.
    
    Règles absolues selon le Guide de Stratégies:
    - Max 1-2% de risque par trade
    - Max 3% de perte journalière
    - Max 6% d'exposition totale
    - Stop trading après 3 pertes consécutives
    """
    
    def __init__(self, config: dict):
        """
        Initialise le Risk Manager.
        
        Args:
            config: Configuration contenant risk_management
        """
        self.config = config.get('risk_management', {})
        
        # Limites de risque
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.01)
        self.max_risk_per_day = self.config.get('max_risk_per_day', 0.03)
        self.max_risk_total = self.config.get('max_risk_total', 0.06)
        self.max_open_positions = self.config.get('max_open_positions', 3)
        
        # Kelly Criterion
        self.kelly_fraction = self.config.get('kelly_fraction', 0.25)  # Quarter-Kelly
        
        # Stop Loss config
        self.sl_config = self.config.get('stop_loss', {})
        self.tp_config = self.config.get('take_profit', {})
        
        # Drawdown config
        self.dd_config = self.config.get('drawdown', {})
        
        # État du trading
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.pause_until: Optional[datetime] = None
        self.trade_history: list = []
        
    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        win_rate: float = 0.5,
        avg_win_loss_ratio: float = 2.0
    ) -> PositionSize:
        """
        Calcule la taille de position optimale.
        
        Méthodes utilisées:
        1. Pourcentage fixe (défaut)
        2. Kelly Criterion (optionnel)
        3. Ajustement ATR (si stop basé sur ATR)
        
        Formule: Position Size = (Capital × Risk%) / Stop Loss Distance
        
        Args:
            capital: Capital disponible
            entry_price: Prix d'entrée prévu
            stop_loss: Niveau de stop-loss
            win_rate: Taux de gain historique (pour Kelly)
            avg_win_loss_ratio: Ratio gain/perte moyen (pour Kelly)
            
        Returns:
            PositionSize avec tous les détails
        """
        # Distance du stop en valeur absolue et pourcentage
        stop_distance = abs(entry_price - stop_loss)
        stop_percent = stop_distance / entry_price
        
        if stop_percent == 0:
            logger.warning("Stop distance is zero, using default 2%")
            stop_percent = 0.02
            stop_distance = entry_price * stop_percent
        
        # Calcul Kelly Criterion
        # Kelly% = W - [(1-W) / R] où W = Win Rate, R = Risk/Reward
        kelly_full = win_rate - ((1 - win_rate) / avg_win_loss_ratio)
        kelly_full = max(0, kelly_full)  # Pas de position négative
        kelly_used = kelly_full * self.kelly_fraction  # Quarter-Kelly
        
        # Utiliser le minimum entre risk fixe et Kelly
        risk_percent = min(self.max_risk_per_trade, kelly_used) if kelly_used > 0 else self.max_risk_per_trade
        
        # Montant à risquer
        risk_amount = capital * risk_percent
        
        # Taille de position (en base currency)
        position_size = risk_amount / stop_distance
        position_size_quote = position_size * entry_price
        
        # Vérification que la position ne dépasse pas l'exposition max
        max_position_quote = capital * self.max_risk_total
        if position_size_quote > max_position_quote:
            position_size_quote = max_position_quote
            position_size = position_size_quote / entry_price
            risk_amount = position_size * stop_distance
            risk_percent = risk_amount / capital
            logger.info(f"Position réduite pour respecter l'exposition max: {position_size_quote:.2f}")
        
        return PositionSize(
            size=round(position_size, 8),
            size_quote=round(position_size_quote, 2),
            risk_amount=round(risk_amount, 2),
            risk_percent=round(risk_percent, 4),
            kelly_full=round(kelly_full, 4),
            kelly_used=round(kelly_used, 4)
        )
    
    def calculate_stop_take_profit(
        self,
        entry_price: float,
        direction: str,  # 'long' ou 'short'
        atr: float,
        style: str = 'swing'  # 'day', 'swing', 'position', 'volatile'
    ) -> StopTakeProfit:
        """
        Calcule les niveaux de stop-loss et take-profit basés sur ATR.
        
        Multiplicateurs ATR par style (selon Guide):
        - Day trading: 1.5-2.0×
        - Swing trading: 2.0-2.5×
        - Position trading: 2.5-3.0×
        - Haute volatilité: 3.0-4.0×
        
        Args:
            entry_price: Prix d'entrée
            direction: 'long' ou 'short'
            atr: Valeur ATR actuelle
            style: Style de trading
            
        Returns:
            StopTakeProfit avec tous les niveaux
        """
        # Sélection du multiplicateur ATR selon le style
        atr_multipliers = {
            'day': self.sl_config.get('atr_multiplier_day', 1.5),
            'swing': self.sl_config.get('atr_multiplier_swing', 2.0),
            'position': self.sl_config.get('atr_multiplier_position', 2.5),
            'volatile': self.sl_config.get('atr_multiplier_volatile', 3.0)
        }
        
        atr_mult = atr_multipliers.get(style, 2.0)
        stop_distance = atr * atr_mult
        
        # Risk/Reward ratio minimum
        min_rr = self.tp_config.get('min_risk_reward_ratio', 2.0)
        take_distance = stop_distance * min_rr
        
        # Calcul des niveaux selon la direction
        if direction == 'long':
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + take_distance
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - take_distance
        
        # Trailing stop (optionnel)
        trailing_stop = None
        if self.tp_config.get('trailing_stop', True):
            trailing_mult = self.tp_config.get('trailing_atr_multiplier', 1.0)
            trailing_stop = atr * trailing_mult
        
        return StopTakeProfit(
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            stop_distance=round(stop_distance, 2),
            take_distance=round(take_distance, 2),
            risk_reward=round(min_rr, 2),
            trailing_stop=round(trailing_stop, 2) if trailing_stop else None
        )
    
    def check_pre_trade_conditions(
        self,
        capital: float,
        current_positions: int,
        current_exposure: float,
        spread_percent: float
    ) -> Tuple[bool, str]:
        """
        Vérifie toutes les conditions pré-trade.
        
        Conditions (selon Guide):
        - daily_loss < MAX_DAILY_DRAWDOWN
        - consecutive_losses < 3
        - total_exposure < 6%
        - spread < 0.2%
        
        Args:
            capital: Capital actuel
            current_positions: Nombre de positions ouvertes
            current_exposure: Exposition actuelle en %
            spread_percent: Spread actuel en %
            
        Returns:
            Tuple (autorisé, raison)
        """
        # Vérifier si en pause
        if self.pause_until and datetime.now() < self.pause_until:
            remaining = (self.pause_until - datetime.now()).seconds // 60
            return False, f"En pause suite à pertes consécutives ({remaining} min restantes)"
        
        # Perte journalière
        daily_loss_limit = self.dd_config.get('daily_loss_limit', 0.03)
        if abs(self.daily_pnl) / capital > daily_loss_limit and self.daily_pnl < 0:
            return False, f"Limite de perte journalière atteinte ({daily_loss_limit*100}%)"
        
        # Pertes consécutives
        max_consecutive = self.dd_config.get('consecutive_loss_pause', 3)
        if self.consecutive_losses >= max_consecutive:
            pause_duration = self.dd_config.get('pause_duration_minutes', 15)
            self.pause_until = datetime.now() + timedelta(minutes=pause_duration)
            return False, f"{max_consecutive} pertes consécutives - pause de {pause_duration} min"
        
        # Nombre de positions
        if current_positions >= self.max_open_positions:
            return False, f"Nombre max de positions atteint ({self.max_open_positions})"
        
        # Exposition totale
        if current_exposure >= self.max_risk_total:
            return False, f"Exposition totale max atteinte ({self.max_risk_total*100}%)"
        
        # Spread
        max_spread = 0.002  # 0.2%
        if spread_percent > max_spread:
            return False, f"Spread trop élevé ({spread_percent*100:.2f}% > {max_spread*100}%)"
        
        return True, "OK"
    
    def update_trade_result(self, pnl: float, capital: float):
        """
        Met à jour les statistiques après un trade.
        
        Args:
            pnl: Profit/Loss du trade
            capital: Capital actuel
        """
        self.daily_pnl += pnl
        self.trade_history.append({
            'pnl': pnl,
            'timestamp': datetime.now(),
            'capital': capital
        })
        
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        logger.info(f"Trade result: PnL={pnl:.2f}, Daily PnL={self.daily_pnl:.2f}, Consec losses={self.consecutive_losses}")
    
    def reset_daily_stats(self):
        """Réinitialise les statistiques journalières."""
        self.daily_pnl = 0.0
        logger.info("Daily stats reset")
    
    def get_scaling_out_levels(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str
    ) -> Dict:
        """
        Calcule les niveaux de scaling out progressif.
        
        Règle (selon Guide):
        - 33% à 1R, déplacer stop au breakeven
        - 33% à 2R, trailing sur le reste
        - 34% final avec trailing stop
        
        Args:
            entry_price: Prix d'entrée
            stop_loss: Niveau de stop
            direction: 'long' ou 'short'
            
        Returns:
            Dict avec les niveaux de scaling
        """
        risk = abs(entry_price - stop_loss)
        
        if direction == 'long':
            level_1 = entry_price + risk  # 1R
            level_2 = entry_price + (risk * 2)  # 2R
            level_3 = entry_price + (risk * 3)  # 3R
        else:
            level_1 = entry_price - risk
            level_2 = entry_price - (risk * 2)
            level_3 = entry_price - (risk * 3)
        
        scaling_config = self.tp_config.get('scaling_out', {})
        
        return {
            'level_1': {
                'price': round(level_1, 2),
                'percent': scaling_config.get('level_1_percent', 0.33),
                'r_multiple': 1,
                'action': 'Prendre 33%, stop au breakeven'
            },
            'level_2': {
                'price': round(level_2, 2),
                'percent': scaling_config.get('level_2_percent', 0.33),
                'r_multiple': 2,
                'action': 'Prendre 33%, activer trailing stop'
            },
            'level_3': {
                'price': round(level_3, 2),
                'percent': scaling_config.get('level_3_percent', 0.34),
                'r_multiple': 3,
                'action': 'Position finale avec trailing'
            }
        }
    
    def get_risk_summary(self, capital: float) -> Dict:
        """
        Retourne un résumé de l'état du risque.
        
        Args:
            capital: Capital actuel
            
        Returns:
            Dict avec le résumé
        """
        return {
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_pnl_percent': round(self.daily_pnl / capital * 100, 2) if capital > 0 else 0,
            'consecutive_losses': self.consecutive_losses,
            'is_paused': self.pause_until is not None and datetime.now() < self.pause_until,
            'pause_remaining_minutes': max(0, (self.pause_until - datetime.now()).seconds // 60) if self.pause_until else 0,
            'max_risk_per_trade': self.max_risk_per_trade,
            'max_daily_loss': self.dd_config.get('daily_loss_limit', 0.03),
            'max_drawdown': self.dd_config.get('max_drawdown', 0.15)
        }
```

### backend/trading/pre_trade_checks.py

```python
"""
Module de vérifications pré-trade.

Implémente toutes les vérifications de sécurité avant d'ouvrir une position
(selon TRADING_STRATEGIES_GUIDE.md).
"""

import logging
from typing import Dict, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PreTradeCheckResult:
    """Résultat d'une vérification pré-trade."""
    passed: bool
    check_name: str
    message: str
    severity: str  # 'info', 'warning', 'critical'


class PreTradeChecker:
    """
    Effectue toutes les vérifications avant d'autoriser un trade.
    
    Vérifications (selon Guide):
    - daily_loss < MAX_DAILY_DRAWDOWN
    - consecutive_losses < 3
    - total_exposure < 6%
    - spread < 0.2%
    - sufficient_liquidity
    - not_in_pause_period
    """
    
    def __init__(self, config: dict):
        """
        Initialise le checker.
        
        Args:
            config: Configuration du bot
        """
        self.config = config
        self.risk_config = config.get('risk_management', {})
        self.safety_config = config.get('manipulation', {}).get('safety', {})
        
    def run_all_checks(
        self,
        capital: float,
        daily_pnl: float,
        consecutive_losses: int,
        open_positions: int,
        total_exposure: float,
        spread: float,
        volume: float,
        avg_volume: float,
        is_paused: bool
    ) -> Tuple[bool, List[PreTradeCheckResult]]:
        """
        Exécute toutes les vérifications pré-trade.
        
        Args:
            capital: Capital actuel
            daily_pnl: P&L journalier
            consecutive_losses: Nombre de pertes consécutives
            open_positions: Nombre de positions ouvertes
            total_exposure: Exposition totale en %
            spread: Spread actuel
            volume: Volume actuel
            avg_volume: Volume moyen
            is_paused: Si le trading est en pause
            
        Returns:
            Tuple (tous_checks_passés, liste_résultats)
        """
        results = []
        
        # Check 1: Pause status
        results.append(self._check_pause_status(is_paused))
        
        # Check 2: Daily loss
        results.append(self._check_daily_loss(daily_pnl, capital))
        
        # Check 3: Consecutive losses
        results.append(self._check_consecutive_losses(consecutive_losses))
        
        # Check 4: Open positions
        results.append(self._check_open_positions(open_positions))
        
        # Check 5: Total exposure
        results.append(self._check_exposure(total_exposure))
        
        # Check 6: Spread
        results.append(self._check_spread(spread))
        
        # Check 7: Liquidity
        results.append(self._check_liquidity(volume, avg_volume))
        
        # Déterminer si tous les checks critiques sont passés
        all_passed = all(r.passed for r in results if r.severity == 'critical')
        
        return all_passed, results
    
    def _check_pause_status(self, is_paused: bool) -> PreTradeCheckResult:
        """Vérifie si le trading n'est pas en pause."""
        if is_paused:
            return PreTradeCheckResult(
                passed=False,
                check_name="pause_status",
                message="Trading en pause suite à pertes consécutives",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="pause_status",
            message="Trading actif",
            severity="info"
        )
    
    def _check_daily_loss(self, daily_pnl: float, capital: float) -> PreTradeCheckResult:
        """Vérifie la perte journalière."""
        max_daily_loss = self.risk_config.get('drawdown', {}).get('daily_loss_limit', 0.03)
        daily_loss_percent = abs(daily_pnl) / capital if capital > 0 else 0
        
        if daily_pnl < 0 and daily_loss_percent >= max_daily_loss:
            return PreTradeCheckResult(
                passed=False,
                check_name="daily_loss",
                message=f"Perte journalière ({daily_loss_percent*100:.1f}%) >= limite ({max_daily_loss*100}%)",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="daily_loss",
            message=f"P&L journalier: {daily_loss_percent*100:.1f}% (limite: {max_daily_loss*100}%)",
            severity="info"
        )
    
    def _check_consecutive_losses(self, consecutive_losses: int) -> PreTradeCheckResult:
        """Vérifie le nombre de pertes consécutives."""
        max_consecutive = self.risk_config.get('drawdown', {}).get('consecutive_loss_pause', 3)
        
        if consecutive_losses >= max_consecutive:
            return PreTradeCheckResult(
                passed=False,
                check_name="consecutive_losses",
                message=f"{consecutive_losses} pertes consécutives >= limite ({max_consecutive})",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="consecutive_losses",
            message=f"{consecutive_losses} pertes consécutives (limite: {max_consecutive})",
            severity="info"
        )
    
    def _check_open_positions(self, open_positions: int) -> PreTradeCheckResult:
        """Vérifie le nombre de positions ouvertes."""
        max_positions = self.risk_config.get('max_open_positions', 3)
        
        if open_positions >= max_positions:
            return PreTradeCheckResult(
                passed=False,
                check_name="open_positions",
                message=f"{open_positions} positions >= max ({max_positions})",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="open_positions",
            message=f"{open_positions}/{max_positions} positions",
            severity="info"
        )
    
    def _check_exposure(self, total_exposure: float) -> PreTradeCheckResult:
        """Vérifie l'exposition totale."""
        max_exposure = self.risk_config.get('max_risk_total', 0.06)
        
        if total_exposure >= max_exposure:
            return PreTradeCheckResult(
                passed=False,
                check_name="exposure",
                message=f"Exposition ({total_exposure*100:.1f}%) >= max ({max_exposure*100}%)",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="exposure",
            message=f"Exposition: {total_exposure*100:.1f}% (max: {max_exposure*100}%)",
            severity="info"
        )
    
    def _check_spread(self, spread: float) -> PreTradeCheckResult:
        """Vérifie le spread."""
        max_spread = self.safety_config.get('max_spread_percent', 0.002)
        
        if spread > max_spread:
            return PreTradeCheckResult(
                passed=False,
                check_name="spread",
                message=f"Spread ({spread*100:.3f}%) > max ({max_spread*100}%)",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="spread",
            message=f"Spread: {spread*100:.3f}% (max: {max_spread*100}%)",
            severity="info"
        )
    
    def _check_liquidity(self, volume: float, avg_volume: float) -> PreTradeCheckResult:
        """Vérifie la liquidité suffisante."""
        if avg_volume == 0:
            return PreTradeCheckResult(
                passed=False,
                check_name="liquidity",
                message="Volume moyen non disponible",
                severity="warning"
            )
        
        volume_ratio = volume / avg_volume
        min_ratio = 0.5  # Volume actuel doit être au moins 50% du moyen
        
        if volume_ratio < min_ratio:
            return PreTradeCheckResult(
                passed=False,
                check_name="liquidity",
                message=f"Volume faible ({volume_ratio*100:.0f}% du moyen)",
                severity="warning"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="liquidity",
            message=f"Volume: {volume_ratio*100:.0f}% du moyen",
            severity="info"
        )
```

---

## 🚀 Instructions de Démarrage

### 1. Créer la structure du projet

```bash
# Créer les dossiers
mkdir -p trading-bot/{config,backend/{api,data,indicators,strategies,trading,analysis,utils},frontend/{public,src/{components,hooks,utils}},data,tests}

# Créer les fichiers __init__.py
touch trading-bot/backend/__init__.py
touch trading-bot/backend/{api,data,indicators,strategies,trading,analysis,utils}/__init__.py
touch trading-bot/tests/__init__.py
```

### 2. Copier le Guide de Stratégies

```bash
# Copier le fichier de référence des stratégies
cp TRADING_STRATEGIES_GUIDE.md trading-bot/
```

### 3. Installer les dépendances Backend

```bash
cd trading-bot

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 4. Installer les dépendances Frontend

```bash
cd frontend
npm install
```

### 5. Configuration

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer selon tes besoins
nano .env
```

### 6. Lancement

```bash
# Terminal 1: Backend
cd trading-bot
source venv/bin/activate
python -m backend.main

# Terminal 2: Frontend
cd trading-bot/frontend
npm run dev
```

### 7. Accès

- **Frontend:** http://localhost:5173
- **API:** http://localhost:8000
- **Docs API:** http://localhost:8000/docs

---

## ⚠️ Avertissements

1. **Paper Trading UNIQUEMENT** - Ce bot est configuré pour la simulation
2. **Pas de clés API en dur** - Utiliser des variables d'environnement
3. **Tester extensivement** avant tout passage en live
4. **Le trading comporte des risques** - Ne jamais investir plus que ce que vous pouvez perdre
5. **Consulter le Guide de Stratégies** - TRADING_STRATEGIES_GUIDE.md contient tous les paramètres et règles

---

## 📈 Fonctionnalités

### Core
- ✅ Dashboard React moderne avec thème sombre
- ✅ Graphiques prix avec indicateurs
- ✅ WebSocket pour mises à jour temps réel

### Indicateurs Techniques
- ✅ RSI avec seuils crypto (20/80)
- ✅ MACD (12/26/9)
- ✅ Bollinger Bands avec détection de squeeze
- ✅ ATR pour stop-loss dynamique
- ✅ EMAs (9, 21, 50) + SMA 200
- ✅ ADX pour filtrer les tendances
- ✅ Stochastic Oscillator

### Smart Money Concepts (ICT)
- ✅ Swing Highs/Lows
- ✅ Order Blocks avec displacement ATR
- ✅ Fair Value Gaps avec midpoint (CE)
- ✅ Break of Structure (BOS)
- ✅ Change of Character (CHoCH)
- ✅ Kill Zones (London, NY, Silver Bullet)

### Analyse Avancée
- ✅ Patterns de chandeliers (Hammer, Engulfing, Star)
- ✅ Divergences RSI/MACD
- ✅ Structure de marché

### Gestion des Risques
- ✅ Position sizing (Kelly Quarter)
- ✅ Stop Loss / Take Profit basés sur ATR
- ✅ Scaling out progressif (33%/33%/34%)
- ✅ Drawdown management
- ✅ Vérifications pré-trade complètes
- ✅ Pause automatique après 3 pertes

### Stratégies
- ✅ Mean Reversion (BB + RSI)
- ✅ EMA Crossover avec confirmation ADX
- ✅ Breakout avec filtre volume
- 🔲 Grid Trading (à activer manuellement)
- 🔲 DCA intelligent (à activer manuellement)

### On-Chain (optionnel)
- 🔲 MVRV Ratio
- 🔲 NUPL
- 🔲 Funding Rates
- 🔲 Whale tracking

---

## 📚 Documentation de Référence

Le fichier **`TRADING_STRATEGIES_GUIDE.md`** contient:
- Configuration optimale de tous les indicateurs
- Formules mathématiques
- Règles d'entrée/sortie précises
- Paramètres de gestion du risque
- Stratégies quantitatives complètes
- Métriques on-chain avec seuils
- Ressources éducatives recommandées

**Toujours consulter ce guide avant de modifier les paramètres du bot.**

---

*Ce fichier est destiné à Claude Code pour créer automatiquement tous les fichiers du projet.*
