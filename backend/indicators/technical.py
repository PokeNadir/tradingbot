"""
Module de calcul des indicateurs techniques.

Indicateurs implémentés (selon logique.md):
- RSI (Relative Strength Index) - période 14, seuils 30/70 ou 20/80 crypto
- MACD (Moving Average Convergence Divergence) - 12/26/9
- Bollinger Bands - période 20, 2.0 écarts-types + %B + Bandwidth
- ATR (Average True Range) - période 14
- EMA/SMA (Moyennes Mobiles) - 9, 21, 50, 200
- DEMA (Double EMA) - Patrick Mulloy
- TEMA (Triple EMA)
- ADX (Average Directional Index) - période 14, seuil 25
- Stochastic Oscillator (Fast, Slow, Full)
- Ichimoku Cloud (Tenkan, Kijun, Senkou A/B, Chikou)
- Parabolic SAR
- VWAP (Volume Weighted Average Price)
- MFI (Money Flow Index)
- CMF (Chaikin Money Flow)
- CCI (Commodity Channel Index)
- Williams %R
- Pivot Points (Standard, Camarilla, Fibonacci)
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.trend import MACD, ADXIndicator, EMAIndicator, SMAIndicator, CCIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import MFIIndicator, ChaikinMoneyFlowIndicator
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
        if df is None or df.empty or len(df) < 20:
            logger.warning(f"Not enough data for indicators: {len(df) if df is not None else 0} rows")
            return df if df is not None else pd.DataFrame()

        df = df.copy()
        try:
            # Core indicators
            df = self.add_rsi(df)
            df = self.add_macd(df)
            df = self.add_bollinger_bands(df)
            df = self.add_atr(df)
            df = self.add_emas(df)
            df = self.add_dema_tema(df)
            df = self.add_adx(df)
            df = self.add_stochastic(df)
            df = self.add_trend_filter(df)
            df = self.add_volume_indicators(df)

            # Advanced indicators from logique.md
            df = self.add_ichimoku(df)
            df = self.add_parabolic_sar(df)
            df = self.add_vwap(df)
            df = self.add_mfi(df)
            df = self.add_cmf(df)
            df = self.add_cci(df)
            df = self.add_williams_r(df)
            df = self.add_pivot_points(df)
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
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

    def add_dema_tema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute DEMA et TEMA (Double/Triple EMA).

        DEMA = 2 × EMA(n) - EMA(EMA(n))
        TEMA = 3 × EMA1 - 3 × EMA2 + EMA3

        Réduit le lag par rapport à l'EMA simple.
        """
        period = 21  # Période standard

        # DEMA: 2 × EMA - EMA(EMA)
        ema1 = df['close'].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        df['dema'] = 2 * ema1 - ema2

        # TEMA: 3 × EMA1 - 3 × EMA2 + EMA3
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        df['tema'] = 3 * ema1 - 3 * ema2 + ema3

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

    def add_ichimoku(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute l'Ichimoku Cloud (Kinko Hyo).

        Tenkan-sen (Conversion) = (Plus Haut 9 + Plus Bas 9) / 2
        Kijun-sen (Base) = (Plus Haut 26 + Plus Bas 26) / 2
        Senkou Span A = (Tenkan + Kijun) / 2 [projeté 26 en avant]
        Senkou Span B = (Plus Haut 52 + Plus Bas 52) / 2 [projeté 26 en avant]
        Chikou Span = Close actuel [tracé 26 en arrière]
        """
        # Paramètres (adaptés pour crypto selon logique.md)
        tenkan_period = 9
        kijun_period = 26
        senkou_b_period = 52
        displacement = 26

        # Tenkan-sen (ligne de conversion)
        high_tenkan = df['high'].rolling(tenkan_period).max()
        low_tenkan = df['low'].rolling(tenkan_period).min()
        df['ichimoku_tenkan'] = (high_tenkan + low_tenkan) / 2

        # Kijun-sen (ligne de base)
        high_kijun = df['high'].rolling(kijun_period).max()
        low_kijun = df['low'].rolling(kijun_period).min()
        df['ichimoku_kijun'] = (high_kijun + low_kijun) / 2

        # Senkou Span A (projeté 26 périodes en avant)
        df['ichimoku_senkou_a'] = ((df['ichimoku_tenkan'] + df['ichimoku_kijun']) / 2).shift(displacement)

        # Senkou Span B (projeté 26 périodes en avant)
        high_senkou = df['high'].rolling(senkou_b_period).max()
        low_senkou = df['low'].rolling(senkou_b_period).min()
        df['ichimoku_senkou_b'] = ((high_senkou + low_senkou) / 2).shift(displacement)

        # Chikou Span (tracé 26 périodes en arrière)
        df['ichimoku_chikou'] = df['close'].shift(-displacement)

        # Kumo (Nuage) - bullish ou bearish
        df['ichimoku_cloud_green'] = df['ichimoku_senkou_a'] > df['ichimoku_senkou_b']
        df['ichimoku_above_cloud'] = df['close'] > df[['ichimoku_senkou_a', 'ichimoku_senkou_b']].max(axis=1)
        df['ichimoku_below_cloud'] = df['close'] < df[['ichimoku_senkou_a', 'ichimoku_senkou_b']].min(axis=1)

        # Signal haussier fort selon logique.md
        df['ichimoku_bullish'] = (
            df['ichimoku_above_cloud'] &
            (df['ichimoku_tenkan'] > df['ichimoku_kijun']) &
            df['ichimoku_cloud_green']
        )

        return df

    def add_parabolic_sar(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le Parabolic SAR.

        SAR_demain = SAR_aujourd'hui + AF × (EP - SAR_aujourd'hui)
        AF démarre à 0.02, incrémente de 0.02, max 0.20
        EP = Extreme Point
        """
        af_start = 0.02
        af_increment = 0.02
        af_max = 0.20

        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        n = len(df)

        psar = np.zeros(n)
        af = np.zeros(n)
        ep = np.zeros(n)
        trend = np.zeros(n)  # 1 = up, -1 = down

        # Initialisation
        psar[0] = close[0]
        af[0] = af_start
        trend[0] = 1
        ep[0] = high[0]

        for i in range(1, n):
            # Calcul du SAR
            if trend[i-1] == 1:  # Tendance haussière
                psar[i] = psar[i-1] + af[i-1] * (ep[i-1] - psar[i-1])
                # SAR ne peut pas être au-dessus des deux derniers lows
                psar[i] = min(psar[i], low[i-1], low[i-2] if i > 1 else low[i-1])

                if low[i] < psar[i]:  # Retournement
                    trend[i] = -1
                    psar[i] = ep[i-1]
                    ep[i] = low[i]
                    af[i] = af_start
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af[i] = min(af[i-1] + af_increment, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
            else:  # Tendance baissière
                psar[i] = psar[i-1] - af[i-1] * (psar[i-1] - ep[i-1])
                # SAR ne peut pas être en-dessous des deux derniers highs
                psar[i] = max(psar[i], high[i-1], high[i-2] if i > 1 else high[i-1])

                if high[i] > psar[i]:  # Retournement
                    trend[i] = 1
                    psar[i] = ep[i-1]
                    ep[i] = high[i]
                    af[i] = af_start
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af[i] = min(af[i-1] + af_increment, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]

        df['psar'] = psar
        df['psar_trend'] = trend
        df['psar_bullish'] = trend == 1

        return df

    def add_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le VWAP (Volume Weighted Average Price).

        VWAP = Σ(Typical Price × Volume) / Σ(Volume)
        Typical Price = (High + Low + Close) / 3
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        cumulative_tp_vol = (typical_price * df['volume']).cumsum()
        cumulative_vol = df['volume'].cumsum()

        df['vwap'] = cumulative_tp_vol / cumulative_vol

        # Bandes VWAP (écart-type pondéré par volume)
        df['vwap_distance'] = (df['close'] - df['vwap']) / df['vwap'] * 100

        # Position par rapport au VWAP
        df['above_vwap'] = df['close'] > df['vwap']
        df['below_vwap'] = df['close'] < df['vwap']

        return df

    def add_mfi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le MFI (Money Flow Index).

        Similar au RSI mais utilise le volume.
        MFI = 100 - (100 / (1 + Money Flow Ratio))
        """
        try:
            mfi = MFIIndicator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                volume=df['volume'],
                window=14
            )
            df['mfi'] = mfi.money_flow_index()
            df['mfi_oversold'] = df['mfi'] < 20
            df['mfi_overbought'] = df['mfi'] > 80
        except Exception as e:
            logger.warning(f"Error calculating MFI: {e}")
            df['mfi'] = np.nan

        return df

    def add_cmf(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le CMF (Chaikin Money Flow).

        CMF = Σ(Money Flow Volume, n) / Σ(Volume, n)
        Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
        """
        try:
            cmf = ChaikinMoneyFlowIndicator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                volume=df['volume'],
                window=20
            )
            df['cmf'] = cmf.chaikin_money_flow()
            df['cmf_bullish'] = df['cmf'] > 0.05
            df['cmf_bearish'] = df['cmf'] < -0.05
        except Exception as e:
            logger.warning(f"Error calculating CMF: {e}")
            df['cmf'] = np.nan

        return df

    def add_cci(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le CCI (Commodity Channel Index).

        CCI = (TP - SMA(TP, n)) / (0.015 × Mean Deviation)
        Seuils: +100/-100 standard, +200/-200 extrême
        """
        try:
            cci = CCIIndicator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=20
            )
            df['cci'] = cci.cci()
            df['cci_overbought'] = df['cci'] > 100
            df['cci_oversold'] = df['cci'] < -100
            df['cci_extreme_high'] = df['cci'] > 200
            df['cci_extreme_low'] = df['cci'] < -200
        except Exception as e:
            logger.warning(f"Error calculating CCI: {e}")
            df['cci'] = np.nan

        return df

    def add_williams_r(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute le Williams %R.

        %R = ((Highest High - Close) / (Highest High - Lowest Low)) × (-100)
        Seuils: -20 suracheté, -80 survendu
        """
        try:
            wr = WilliamsRIndicator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                lbp=14
            )
            df['williams_r'] = wr.williams_r()
            df['williams_overbought'] = df['williams_r'] > -20
            df['williams_oversold'] = df['williams_r'] < -80
        except Exception as e:
            logger.warning(f"Error calculating Williams %R: {e}")
            df['williams_r'] = np.nan

        return df

    def add_pivot_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute les Pivot Points (Standard, Camarilla, Fibonacci).

        Standard: PP = (H + L + C) / 3
        """
        # On utilise les données de la période précédente pour calculer les pivots
        prev_high = df['high'].shift(1)
        prev_low = df['low'].shift(1)
        prev_close = df['close'].shift(1)

        # Pivot Point Standard
        pp = (prev_high + prev_low + prev_close) / 3
        df['pivot_pp'] = pp

        # Résistances et Supports Standard
        df['pivot_r1'] = (2 * pp) - prev_low
        df['pivot_r2'] = pp + (prev_high - prev_low)
        df['pivot_r3'] = df['pivot_r2'] + (prev_high - prev_low)

        df['pivot_s1'] = (2 * pp) - prev_high
        df['pivot_s2'] = pp - (prev_high - prev_low)
        df['pivot_s3'] = df['pivot_s2'] - (prev_high - prev_low)

        # Pivot Points Fibonacci
        range_hl = prev_high - prev_low
        df['pivot_fib_r1'] = pp + (range_hl * 0.382)
        df['pivot_fib_r2'] = pp + (range_hl * 0.618)
        df['pivot_fib_r3'] = pp + range_hl

        df['pivot_fib_s1'] = pp - (range_hl * 0.382)
        df['pivot_fib_s2'] = pp - (range_hl * 0.618)
        df['pivot_fib_s3'] = pp - range_hl

        # Pivot Points Camarilla
        df['pivot_cam_r1'] = prev_close + (range_hl * 1.1 / 12)
        df['pivot_cam_r2'] = prev_close + (range_hl * 1.1 / 6)
        df['pivot_cam_r3'] = prev_close + (range_hl * 1.1 / 4)
        df['pivot_cam_r4'] = prev_close + (range_hl * 1.1 / 2)

        df['pivot_cam_s1'] = prev_close - (range_hl * 1.1 / 12)
        df['pivot_cam_s2'] = prev_close - (range_hl * 1.1 / 6)
        df['pivot_cam_s3'] = prev_close - (range_hl * 1.1 / 4)
        df['pivot_cam_s4'] = prev_close - (range_hl * 1.1 / 2)

        return df

    def get_current_values(self, df: pd.DataFrame) -> Dict:
        """
        Récupère les valeurs actuelles de tous les indicateurs.

        Args:
            df: DataFrame avec indicateurs calculés

        Returns:
            Dict avec les valeurs actuelles
        """
        if df is None or df.empty or len(df) == 0:
            return {}

        try:
            last = df.iloc[-1]
        except (IndexError, KeyError):
            return {}

        def safe_round(val, decimals=2):
            return round(val, decimals) if pd.notna(val) else None

        return {
            # Core indicators
            'rsi': safe_round(last.get('rsi', 0)),
            'rsi_oversold': bool(last.get('rsi_oversold', False)),
            'rsi_overbought': bool(last.get('rsi_overbought', False)),
            'macd': safe_round(last.get('macd', 0), 4),
            'macd_signal': safe_round(last.get('macd_signal', 0), 4),
            'macd_histogram': safe_round(last.get('macd_histogram', 0), 4),
            'bb_upper': safe_round(last.get('bb_upper', 0)),
            'bb_middle': safe_round(last.get('bb_middle', 0)),
            'bb_lower': safe_round(last.get('bb_lower', 0)),
            'bb_percent': safe_round(last.get('bb_percent', 0), 4),
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

            # Moving averages
            'ema_9': safe_round(last.get('ema_9', 0)),
            'ema_21': safe_round(last.get('ema_21', 0)),
            'ema_50': safe_round(last.get('ema_50', 0)),
            'sma_200': safe_round(last.get('sma_200', 0)),
            'dema': safe_round(last.get('dema', 0)),
            'tema': safe_round(last.get('tema', 0)),
            'trend_bias': int(last.get('trend_bias', 0)) if pd.notna(last.get('trend_bias')) else 0,
            'above_sma200': bool(last.get('above_sma200', False)),

            # Ichimoku
            'ichimoku_tenkan': safe_round(last.get('ichimoku_tenkan', 0)),
            'ichimoku_kijun': safe_round(last.get('ichimoku_kijun', 0)),
            'ichimoku_above_cloud': bool(last.get('ichimoku_above_cloud', False)),
            'ichimoku_bullish': bool(last.get('ichimoku_bullish', False)),

            # Parabolic SAR
            'psar': safe_round(last.get('psar', 0)),
            'psar_bullish': bool(last.get('psar_bullish', False)),

            # Volume indicators
            'vwap': safe_round(last.get('vwap', 0)),
            'vwap_distance': safe_round(last.get('vwap_distance', 0), 4),
            'above_vwap': bool(last.get('above_vwap', False)),
            'mfi': safe_round(last.get('mfi', 0)),
            'mfi_oversold': bool(last.get('mfi_oversold', False)),
            'mfi_overbought': bool(last.get('mfi_overbought', False)),
            'cmf': safe_round(last.get('cmf', 0), 4),
            'cmf_bullish': bool(last.get('cmf_bullish', False)),
            'volume_ratio': safe_round(last.get('volume_ratio', 0)),
            'high_volume': bool(last.get('high_volume', False)),

            # Additional oscillators
            'cci': safe_round(last.get('cci', 0)),
            'cci_overbought': bool(last.get('cci_overbought', False)),
            'cci_oversold': bool(last.get('cci_oversold', False)),
            'williams_r': safe_round(last.get('williams_r', 0)),
            'williams_overbought': bool(last.get('williams_overbought', False)),
            'williams_oversold': bool(last.get('williams_oversold', False)),

            # Pivot Points
            'pivot_pp': safe_round(last.get('pivot_pp', 0)),
            'pivot_r1': safe_round(last.get('pivot_r1', 0)),
            'pivot_s1': safe_round(last.get('pivot_s1', 0)),

            # Price/Volume
            'close': safe_round(last.get('close', 0)),
            'volume': safe_round(last.get('volume', 0))
        }
