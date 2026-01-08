"""
Module d'analyse de structure de marché.

Analyse les tendances, les niveaux clés et le biais de marché.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketLevel:
    """Niveau de prix clé."""
    price: float
    type: str  # 'support', 'resistance', 'pivot'
    strength: int  # Nombre de touches
    last_touch: int  # Index de la dernière touche


class MarketStructureAnalyzer:
    """
    Analyse la structure globale du marché.

    Identifie:
    - Tendance (uptrend, downtrend, ranging)
    - Supports et résistances
    - Points pivots
    - Biais de trading
    """

    def __init__(self, config: dict):
        """
        Initialise l'analyseur.

        Args:
            config: Configuration du bot
        """
        self.config = config
        self.levels: List[MarketLevel] = []

    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """
        Analyse la tendance du marché.

        Méthodes utilisées:
        - Position par rapport aux EMAs
        - Higher highs / Lower lows
        - ADX pour la force de tendance

        Args:
            df: DataFrame avec indicateurs

        Returns:
            Dict avec l'analyse de tendance
        """
        if df.empty or len(df) < 50:
            return {'trend': 'unknown', 'strength': 0}

        last = df.iloc[-1]

        # Analyse EMA
        above_ema_50 = last['close'] > last.get('ema_50', last['close'])
        above_sma_200 = last['close'] > last.get('sma_200', last['close'])

        # Analyse des highs/lows récents
        recent = df.iloc[-20:]
        highs = recent['high'].values
        lows = recent['low'].values

        higher_highs = self._count_higher_highs(highs)
        higher_lows = self._count_higher_lows(lows)
        lower_highs = self._count_lower_highs(highs)
        lower_lows = self._count_lower_lows(lows)

        # Déterminer la tendance
        hh_hl_score = higher_highs + higher_lows
        lh_ll_score = lower_highs + lower_lows

        if hh_hl_score > lh_ll_score + 2:
            trend = 'uptrend'
        elif lh_ll_score > hh_hl_score + 2:
            trend = 'downtrend'
        else:
            trend = 'ranging'

        # Force de la tendance (ADX)
        adx = last.get('adx', 20)
        if adx > 40:
            strength = 'strong'
        elif adx > 25:
            strength = 'moderate'
        else:
            strength = 'weak'

        # Biais de trading
        if trend == 'uptrend' and above_sma_200:
            bias = 'strongly_bullish'
        elif trend == 'uptrend' or above_sma_200:
            bias = 'bullish'
        elif trend == 'downtrend' and not above_sma_200:
            bias = 'strongly_bearish'
        elif trend == 'downtrend' or not above_sma_200:
            bias = 'bearish'
        else:
            bias = 'neutral'

        return {
            'trend': trend,
            'strength': strength,
            'bias': bias,
            'adx': round(adx, 2) if pd.notna(adx) else None,
            'above_ema_50': above_ema_50,
            'above_sma_200': above_sma_200,
            'higher_highs': higher_highs,
            'higher_lows': higher_lows,
            'lower_highs': lower_highs,
            'lower_lows': lower_lows
        }

    def _count_higher_highs(self, highs: np.ndarray) -> int:
        """Compte les higher highs consécutifs."""
        count = 0
        for i in range(1, len(highs)):
            if highs[i] > highs[i-1]:
                count += 1
        return count

    def _count_higher_lows(self, lows: np.ndarray) -> int:
        """Compte les higher lows consécutifs."""
        count = 0
        for i in range(1, len(lows)):
            if lows[i] > lows[i-1]:
                count += 1
        return count

    def _count_lower_highs(self, highs: np.ndarray) -> int:
        """Compte les lower highs consécutifs."""
        count = 0
        for i in range(1, len(highs)):
            if highs[i] < highs[i-1]:
                count += 1
        return count

    def _count_lower_lows(self, lows: np.ndarray) -> int:
        """Compte les lower lows consécutifs."""
        count = 0
        for i in range(1, len(lows)):
            if lows[i] < lows[i-1]:
                count += 1
        return count

    def find_support_resistance(
        self,
        df: pd.DataFrame,
        num_levels: int = 5
    ) -> Dict:
        """
        Identifie les niveaux de support et résistance.

        Args:
            df: DataFrame OHLCV
            num_levels: Nombre de niveaux à retourner

        Returns:
            Dict avec supports et résistances
        """
        if df.empty or len(df) < 20:
            return {'supports': [], 'resistances': []}

        current_price = df['close'].iloc[-1]
        all_levels = []

        # Méthode 1: Pivots locaux
        for i in range(5, len(df) - 5):
            # Swing high
            if df['high'].iloc[i] == df['high'].iloc[i-5:i+6].max():
                all_levels.append({
                    'price': df['high'].iloc[i],
                    'type': 'resistance' if df['high'].iloc[i] > current_price else 'support',
                    'method': 'swing',
                    'strength': 1
                })

            # Swing low
            if df['low'].iloc[i] == df['low'].iloc[i-5:i+6].min():
                all_levels.append({
                    'price': df['low'].iloc[i],
                    'type': 'support' if df['low'].iloc[i] < current_price else 'resistance',
                    'method': 'swing',
                    'strength': 1
                })

        # Méthode 2: EMAs comme support/résistance dynamique
        for ema_col in ['ema_21', 'ema_50', 'sma_200']:
            if ema_col in df.columns:
                ema_value = df[ema_col].iloc[-1]
                if pd.notna(ema_value):
                    all_levels.append({
                        'price': ema_value,
                        'type': 'support' if ema_value < current_price else 'resistance',
                        'method': 'ema',
                        'strength': 2 if ema_col == 'sma_200' else 1
                    })

        # Méthode 3: Bollinger Bands
        if 'bb_upper' in df.columns:
            all_levels.append({
                'price': df['bb_upper'].iloc[-1],
                'type': 'resistance',
                'method': 'bollinger',
                'strength': 1
            })
            all_levels.append({
                'price': df['bb_lower'].iloc[-1],
                'type': 'support',
                'method': 'bollinger',
                'strength': 1
            })

        # Consolider les niveaux proches
        consolidated = self._consolidate_levels(all_levels, tolerance=0.01)

        # Séparer supports et résistances
        supports = sorted(
            [l for l in consolidated if l['type'] == 'support'],
            key=lambda x: x['price'],
            reverse=True
        )[:num_levels]

        resistances = sorted(
            [l for l in consolidated if l['type'] == 'resistance'],
            key=lambda x: x['price']
        )[:num_levels]

        return {
            'current_price': round(current_price, 2),
            'supports': [
                {'price': round(s['price'], 2), 'strength': s['strength']}
                for s in supports
            ],
            'resistances': [
                {'price': round(r['price'], 2), 'strength': r['strength']}
                for r in resistances
            ]
        }

    def _consolidate_levels(
        self,
        levels: List[Dict],
        tolerance: float = 0.01
    ) -> List[Dict]:
        """
        Consolide les niveaux proches.

        Args:
            levels: Liste des niveaux
            tolerance: Tolérance en pourcentage

        Returns:
            Liste consolidée
        """
        if not levels:
            return []

        # Trier par prix
        sorted_levels = sorted(levels, key=lambda x: x['price'])
        consolidated = []

        current_group = [sorted_levels[0]]

        for level in sorted_levels[1:]:
            avg_price = sum(l['price'] for l in current_group) / len(current_group)
            if abs(level['price'] - avg_price) / avg_price < tolerance:
                current_group.append(level)
            else:
                # Finaliser le groupe actuel
                consolidated.append({
                    'price': sum(l['price'] for l in current_group) / len(current_group),
                    'type': current_group[0]['type'],
                    'strength': sum(l['strength'] for l in current_group)
                })
                current_group = [level]

        # Ajouter le dernier groupe
        if current_group:
            consolidated.append({
                'price': sum(l['price'] for l in current_group) / len(current_group),
                'type': current_group[0]['type'],
                'strength': sum(l['strength'] for l in current_group)
            })

        return consolidated

    def get_market_phase(self, df: pd.DataFrame) -> Dict:
        """
        Identifie la phase de marché (Wyckoff).

        Phases:
        - Accumulation: après une baisse, range avec volume croissant
        - Markup: tendance haussière
        - Distribution: après une hausse, range avec volume décroissant
        - Markdown: tendance baissière

        Args:
            df: DataFrame avec indicateurs

        Returns:
            Dict avec la phase identifiée
        """
        if df.empty or len(df) < 50:
            return {'phase': 'unknown'}

        trend = self.analyze_trend(df)
        last = df.iloc[-1]

        # Analyse du volume
        volume_trend = 'increasing' if last.get('volume_ratio', 1) > 1.2 else 'decreasing'
        is_ranging = trend['trend'] == 'ranging'

        # Déterminer la phase
        if is_ranging and last['close'] < df['close'].rolling(50).mean().iloc[-1]:
            phase = 'accumulation'
            description = 'Phase d\'accumulation - range après baisse'
        elif trend['trend'] == 'uptrend' and trend['strength'] in ['moderate', 'strong']:
            phase = 'markup'
            description = 'Phase de markup - tendance haussière active'
        elif is_ranging and last['close'] > df['close'].rolling(50).mean().iloc[-1]:
            phase = 'distribution'
            description = 'Phase de distribution - range après hausse'
        elif trend['trend'] == 'downtrend' and trend['strength'] in ['moderate', 'strong']:
            phase = 'markdown'
            description = 'Phase de markdown - tendance baissière active'
        else:
            phase = 'transition'
            description = 'Phase de transition'

        return {
            'phase': phase,
            'description': description,
            'volume_trend': volume_trend,
            'trend': trend['trend'],
            'bias': trend['bias']
        }
