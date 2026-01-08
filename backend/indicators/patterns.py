"""
Module de détection des patterns de chandeliers japonais.

Patterns implémentés (selon TRADING_STRATEGIES_GUIDE.md):
- Hammer (fiabilité 8/10)
- Engulfing (fiabilité 9/10)
- Morning/Evening Star (fiabilité 9/10)
- Doji
- Shooting Star
- Three White Soldiers / Three Black Crows
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

        if len(df) < 3:
            return patterns

        # Détection sur les dernières bougies
        hammer = self.detect_hammer(df)
        if hammer:
            patterns.append(hammer)

        shooting_star = self.detect_shooting_star(df)
        if shooting_star:
            patterns.append(shooting_star)

        engulfing = self.detect_engulfing(df)
        if engulfing:
            patterns.append(engulfing)

        star = self.detect_star(df)
        if star:
            patterns.append(star)

        doji = self.detect_doji(df)
        if doji:
            patterns.append(doji)

        three_soldiers = self.detect_three_soldiers(df)
        if three_soldiers:
            patterns.append(three_soldiers)

        three_crows = self.detect_three_crows(df)
        if three_crows:
            patterns.append(three_crows)

        return patterns

    def detect_hammer(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte un Hammer (marteau).

        Critères (fiabilité 8/10):
        - Mèche inférieure ≥ 2× corps
        - Mèche supérieure ≤ 10% du range
        - Doit apparaître en bas de tendance baissière
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

    def detect_shooting_star(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte un Shooting Star (étoile filante).

        Critères:
        - Mèche supérieure ≥ 2× corps
        - Mèche inférieure ≤ 10% du range
        - Doit apparaître en haut de tendance haussière
        """
        if len(df) < 10:
            return None

        last = df.iloc[-1]

        body = abs(last['close'] - last['open'])
        total_range = last['high'] - last['low']

        if total_range == 0:
            return None

        upper_wick = last['high'] - max(last['open'], last['close'])
        lower_wick = min(last['open'], last['close']) - last['low']

        if upper_wick >= (2 * body) and lower_wick <= (0.1 * total_range):
            # Vérifier tendance haussière précédente
            prev_closes = df['close'].iloc[-10:-1]
            if prev_closes.iloc[-1] > prev_closes.iloc[0]:
                return CandlePattern(
                    name="Shooting Star",
                    type="bearish",
                    index=len(df) - 1,
                    confidence=0.8,
                    description="Étoile filante détectée en haut de tendance - signal de retournement baissier"
                )

        return None

    def detect_engulfing(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte un Engulfing (engloutissante).

        Critères (fiabilité 9/10):
        - Le corps de la bougie actuelle englobe entièrement le corps précédent
        """
        if len(df) < 2:
            return None

        current = df.iloc[-1]
        prev = df.iloc[-2]

        current_body = abs(current['close'] - current['open'])
        prev_body = abs(prev['close'] - prev['open'])

        config = self.config.get('engulfing', {})
        min_body_ratio = config.get('min_body_ratio', 0.6)

        current_range = current['high'] - current['low']
        if current_range == 0 or (current_body / current_range) < min_body_ratio:
            return None

        # Bullish Engulfing
        if (current['close'] > current['open'] and
            prev['close'] < prev['open'] and
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
        if (current['close'] < current['open'] and
            prev['close'] > prev['open'] and
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

        first_range = first['high'] - first['low']
        middle_range = middle['high'] - middle['low']

        if first_range == 0 or middle_range == 0:
            return None

        # Bougie centrale doit être petite (< 30% du range)
        if (middle_body / middle_range) > 0.3:
            return None

        first_midpoint = (first['open'] + first['close']) / 2

        # Morning Star (bullish)
        if (first['close'] < first['open'] and
            last['close'] > last['open'] and
            last['close'] > first_midpoint):
            return CandlePattern(
                name="Morning Star",
                type="bullish",
                index=len(df) - 1,
                confidence=0.9,
                description="Étoile du matin - signal de retournement haussier fort"
            )

        # Evening Star (bearish)
        if (first['close'] > first['open'] and
            last['close'] < last['open'] and
            last['close'] < first_midpoint):
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

    def detect_three_soldiers(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte Three White Soldiers (Trois soldats blancs).

        Critères:
        - 3 bougies haussières consécutives
        - Chaque ouverture est dans le corps de la bougie précédente
        - Chaque clôture est proche du plus haut
        """
        if len(df) < 3:
            return None

        candles = df.iloc[-3:]

        # Vérifier que toutes sont haussières
        all_bullish = all(c['close'] > c['open'] for _, c in candles.iterrows())
        if not all_bullish:
            return None

        # Vérifier la progression
        closes_rising = (
            candles.iloc[0]['close'] < candles.iloc[1]['close'] < candles.iloc[2]['close']
        )
        if not closes_rising:
            return None

        # Vérifier les ouvertures dans le corps précédent
        valid_opens = (
            candles.iloc[0]['close'] > candles.iloc[1]['open'] > candles.iloc[0]['open'] and
            candles.iloc[1]['close'] > candles.iloc[2]['open'] > candles.iloc[1]['open']
        )
        if not valid_opens:
            return None

        return CandlePattern(
            name="Three White Soldiers",
            type="bullish",
            index=len(df) - 1,
            confidence=0.85,
            description="Trois soldats blancs - fort signal haussier"
        )

    def detect_three_crows(self, df: pd.DataFrame) -> Optional[CandlePattern]:
        """
        Détecte Three Black Crows (Trois corbeaux noirs).

        Critères:
        - 3 bougies baissières consécutives
        - Chaque ouverture est dans le corps de la bougie précédente
        - Chaque clôture est proche du plus bas
        """
        if len(df) < 3:
            return None

        candles = df.iloc[-3:]

        # Vérifier que toutes sont baissières
        all_bearish = all(c['close'] < c['open'] for _, c in candles.iterrows())
        if not all_bearish:
            return None

        # Vérifier la progression
        closes_falling = (
            candles.iloc[0]['close'] > candles.iloc[1]['close'] > candles.iloc[2]['close']
        )
        if not closes_falling:
            return None

        # Vérifier les ouvertures dans le corps précédent
        valid_opens = (
            candles.iloc[0]['close'] < candles.iloc[1]['open'] < candles.iloc[0]['open'] and
            candles.iloc[1]['close'] < candles.iloc[2]['open'] < candles.iloc[1]['open']
        )
        if not valid_opens:
            return None

        return CandlePattern(
            name="Three Black Crows",
            type="bearish",
            index=len(df) - 1,
            confidence=0.85,
            description="Trois corbeaux noirs - fort signal baissier"
        )

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
        df['pattern_confidence'] = 0.0

        for i in range(3, len(df)):
            subset = df.iloc[:i+1].copy()
            patterns = self.detect_all(subset)

            for pattern in patterns:
                if pattern.type == 'bullish':
                    df.iloc[i, df.columns.get_loc('pattern_bullish')] = True
                elif pattern.type == 'bearish':
                    df.iloc[i, df.columns.get_loc('pattern_bearish')] = True

                df.iloc[i, df.columns.get_loc('pattern_name')] = pattern.name
                df.iloc[i, df.columns.get_loc('pattern_confidence')] = pattern.confidence

        return df

    def get_patterns_summary(self, df: pd.DataFrame) -> Dict:
        """
        Retourne un résumé des patterns détectés.

        Args:
            df: DataFrame OHLCV

        Returns:
            Dict avec les patterns et leur signification
        """
        patterns = self.detect_all(df)

        return {
            'count': len(patterns),
            'patterns': [
                {
                    'name': p.name,
                    'type': p.type,
                    'confidence': p.confidence,
                    'description': p.description
                }
                for p in patterns
            ],
            'bullish_count': sum(1 for p in patterns if p.type == 'bullish'),
            'bearish_count': sum(1 for p in patterns if p.type == 'bearish'),
            'has_strong_signal': any(p.confidence >= 0.85 for p in patterns)
        }
