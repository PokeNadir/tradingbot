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

    def add_divergence_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute des colonnes de divergence au DataFrame.

        Args:
            df: DataFrame avec indicateurs

        Returns:
            DataFrame avec colonnes divergence_*
        """
        df = df.copy()
        df['divergence_bullish'] = False
        df['divergence_bearish'] = False
        df['divergence_type'] = ''

        divergences = self.detect_all(df)

        for div in divergences:
            if 'bullish' in div.type:
                df.iloc[div.end_index, df.columns.get_loc('divergence_bullish')] = True
            else:
                df.iloc[div.end_index, df.columns.get_loc('divergence_bearish')] = True
            df.iloc[div.end_index, df.columns.get_loc('divergence_type')] = div.type

        return df

    def get_divergences_summary(self, df: pd.DataFrame) -> Dict:
        """
        Retourne un résumé des divergences détectées.

        Args:
            df: DataFrame avec indicateurs

        Returns:
            Dict avec les divergences et leur signification
        """
        divergences = self.detect_all(df)

        return {
            'count': len(divergences),
            'divergences': [
                {
                    'type': d.type,
                    'indicator': d.indicator,
                    'confidence': d.confidence,
                    'description': d.description
                }
                for d in divergences
            ],
            'bullish_count': sum(1 for d in divergences if 'bullish' in d.type),
            'bearish_count': sum(1 for d in divergences if 'bearish' in d.type),
            'has_reversal_signal': any(d.type.startswith('regular') for d in divergences)
        }
