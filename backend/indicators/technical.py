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
        df = self.add_volume_indicators(df)
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

        # Ajout des conditions de surachat/survente
        oversold = self.config.get('rsi', {}).get('oversold', 30)
        overbought = self.config.get('rsi', {}).get('overbought', 70)
        df['rsi_oversold'] = df['rsi'] < oversold
        df['rsi_overbought'] = df['rsi'] > overbought

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

        # Crossovers
        df['macd_cross_up'] = (
            (df['macd'] > df['macd_signal']) &
            (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        )
        df['macd_cross_down'] = (
            (df['macd'] < df['macd_signal']) &
            (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        )

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

        # Position par rapport aux bandes
        df['below_bb_lower'] = df['close'] < df['bb_lower']
        df['above_bb_upper'] = df['close'] > df['bb_upper']

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

        # Niveaux de volatilité
        atr_sma = df['atr'].rolling(50).mean()
        df['high_volatility'] = df['atr'] > atr_sma * 1.5
        df['low_volatility'] = df['atr'] < atr_sma * 0.75

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

        # EMA crossovers
        df['ema_cross_up'] = (
            (df['ema_9'] > df['ema_21']) &
            (df['ema_9'].shift(1) <= df['ema_21'].shift(1))
        )
        df['ema_cross_down'] = (
            (df['ema_9'] < df['ema_21']) &
            (df['ema_9'].shift(1) >= df['ema_21'].shift(1))
        )

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
        df['ranging'] = df['adx'] < 20

        # Direction de la tendance
        df['trend_up'] = df['adx_pos'] > df['adx_neg']
        df['trend_down'] = df['adx_pos'] < df['adx_neg']

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

        # Zones
        oversold = stoch_config.get('oversold', 20)
        overbought = stoch_config.get('overbought', 80)
        df['stoch_oversold'] = df['stoch_k'] < oversold
        df['stoch_overbought'] = df['stoch_k'] > overbought

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

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute des indicateurs de volume.
        """
        # Volume SMA
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['high_volume'] = df['volume_ratio'] > 1.5

        # On-Balance Volume simplifiée
        df['obv'] = (
            np.sign(df['close'].diff()) * df['volume']
        ).cumsum()

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

        def safe_round(val, decimals=2):
            return round(val, decimals) if pd.notna(val) else None

        return {
            'rsi': safe_round(last.get('rsi', 0)),
            'rsi_oversold': bool(last.get('rsi_oversold', False)),
            'rsi_overbought': bool(last.get('rsi_overbought', False)),
            'macd': safe_round(last.get('macd', 0), 4),
            'macd_signal': safe_round(last.get('macd_signal', 0), 4),
            'macd_histogram': safe_round(last.get('macd_histogram', 0), 4),
            'bb_upper': safe_round(last.get('bb_upper', 0)),
            'bb_middle': safe_round(last.get('bb_middle', 0)),
            'bb_lower': safe_round(last.get('bb_lower', 0)),
            'bb_squeeze': bool(last.get('bb_squeeze', False)),
            'atr': safe_round(last.get('atr', 0)),
            'atr_percent': safe_round(last.get('atr_percent', 0), 4),
            'high_volatility': bool(last.get('high_volatility', False)),
            'adx': safe_round(last.get('adx', 0)),
            'trending': bool(last.get('trending', False)),
            'ranging': bool(last.get('ranging', False)),
            'trend_up': bool(last.get('trend_up', False)),
            'stoch_k': safe_round(last.get('stoch_k', 0)),
            'stoch_d': safe_round(last.get('stoch_d', 0)),
            'ema_9': safe_round(last.get('ema_9', 0)),
            'ema_21': safe_round(last.get('ema_21', 0)),
            'ema_50': safe_round(last.get('ema_50', 0)),
            'sma_200': safe_round(last.get('sma_200', 0)),
            'trend_bias': int(last.get('trend_bias', 0)) if pd.notna(last.get('trend_bias')) else 0,
            'above_sma200': bool(last.get('above_sma200', False)),
            'close': safe_round(last.get('close', 0)),
            'volume': safe_round(last.get('volume', 0)),
            'volume_ratio': safe_round(last.get('volume_ratio', 0)),
            'high_volume': bool(last.get('high_volume', False))
        }
