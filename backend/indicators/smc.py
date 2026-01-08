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
from datetime import datetime
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
                timestamp = df.index[i] if isinstance(df.index, pd.DatetimeIndex) else pd.Timestamp.now()
                self.swing_highs.append(SwingPoint(
                    i, df['high'].iloc[i], timestamp, 'high'
                ))

            # Swing low
            window_low = df['low'].iloc[i-self.swing_length:i+self.swing_length+1].min()
            if df['low'].iloc[i] == window_low:
                df.iloc[i, df.columns.get_loc('swing_low')] = df['low'].iloc[i]
                timestamp = df.index[i] if isinstance(df.index, pd.DatetimeIndex) else pd.Timestamp.now()
                self.swing_lows.append(SwingPoint(
                    i, df['low'].iloc[i], timestamp, 'low'
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
            vol_threshold = avg_volume.iloc[i] * self.ob_volume_threshold if pd.notna(avg_volume.iloc[i]) else 0
            if current['volume'] < vol_threshold:
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
            'recent_choch': len([sb for sb in self.structure_breaks if 'choch' in sb.type]),
            'last_swing_high': self.swing_highs[-1].price if self.swing_highs else None,
            'last_swing_low': self.swing_lows[-1].price if self.swing_lows else None
        }
