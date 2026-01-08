"""
Module d'analyse du Volume Profile.

Identifie:
- POC (Point of Control)
- Value Area (70% du volume)
- HVN (High Volume Nodes)
- LVN (Low Volume Nodes)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VolumeLevel:
    """Niveau de volume."""
    price: float
    volume: float
    percentage: float


class VolumeProfileAnalyzer:
    """
    Analyse le Volume Profile pour identifier les niveaux clés.

    Le Volume Profile montre la distribution du volume à différents niveaux de prix,
    révélant où les participants ont été les plus actifs.
    """

    def __init__(self, config: dict, num_bins: int = 50):
        """
        Initialise l'analyseur.

        Args:
            config: Configuration du bot
            num_bins: Nombre de niveaux de prix à analyser
        """
        self.config = config
        self.num_bins = num_bins

    def calculate_profile(self, df: pd.DataFrame) -> Dict:
        """
        Calcule le Volume Profile.

        Args:
            df: DataFrame OHLCV

        Returns:
            Dict avec le profile calculé
        """
        if df.empty or len(df) < 10:
            return {'error': 'Données insuffisantes'}

        # Définir les bins de prix
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_range = price_max - price_min

        if price_range == 0:
            return {'error': 'Range de prix nul'}

        bin_size = price_range / self.num_bins
        bins = np.linspace(price_min, price_max, self.num_bins + 1)

        # Calculer le volume à chaque niveau
        volume_at_price = np.zeros(self.num_bins)

        for _, row in df.iterrows():
            # Distribuer le volume de la bougie sur les niveaux qu'elle touche
            low_bin = int((row['low'] - price_min) / bin_size)
            high_bin = int((row['high'] - price_min) / bin_size)

            low_bin = max(0, min(low_bin, self.num_bins - 1))
            high_bin = max(0, min(high_bin, self.num_bins - 1))

            # Distribuer le volume uniformément
            num_bins_touched = high_bin - low_bin + 1
            vol_per_bin = row['volume'] / num_bins_touched

            for b in range(low_bin, high_bin + 1):
                if b < self.num_bins:
                    volume_at_price[b] += vol_per_bin

        # Calculer les statistiques
        total_volume = volume_at_price.sum()

        # POC (Point of Control) - niveau avec le plus de volume
        poc_bin = np.argmax(volume_at_price)
        poc_price = bins[poc_bin] + bin_size / 2

        # Value Area (70% du volume)
        va_high, va_low = self._calculate_value_area(
            volume_at_price, bins, bin_size, total_volume
        )

        # HVN et LVN
        hvn, lvn = self._find_volume_nodes(
            volume_at_price, bins, bin_size, total_volume
        )

        # Construire le profile
        profile = []
        for i in range(self.num_bins):
            price = bins[i] + bin_size / 2
            vol = volume_at_price[i]
            pct = vol / total_volume * 100 if total_volume > 0 else 0
            profile.append({
                'price': round(price, 2),
                'volume': round(vol, 2),
                'percentage': round(pct, 2)
            })

        return {
            'poc': round(poc_price, 2),
            'value_area_high': round(va_high, 2),
            'value_area_low': round(va_low, 2),
            'hvn': hvn,
            'lvn': lvn,
            'profile': profile,
            'total_volume': round(total_volume, 2),
            'price_range': {
                'min': round(price_min, 2),
                'max': round(price_max, 2)
            }
        }

    def _calculate_value_area(
        self,
        volume_at_price: np.ndarray,
        bins: np.ndarray,
        bin_size: float,
        total_volume: float
    ) -> Tuple[float, float]:
        """
        Calcule la Value Area (70% du volume).

        La Value Area est la zone où 70% du volume a été échangé.

        Args:
            volume_at_price: Volume à chaque niveau
            bins: Niveaux de prix
            bin_size: Taille d'un bin
            total_volume: Volume total

        Returns:
            Tuple (VA High, VA Low)
        """
        target_volume = total_volume * 0.70
        poc_bin = np.argmax(volume_at_price)

        # Commencer du POC et étendre vers les deux côtés
        va_volume = volume_at_price[poc_bin]
        upper = poc_bin
        lower = poc_bin

        while va_volume < target_volume:
            # Comparer les volumes au-dessus et en dessous
            vol_above = volume_at_price[upper + 1] if upper + 1 < len(volume_at_price) else 0
            vol_below = volume_at_price[lower - 1] if lower - 1 >= 0 else 0

            if vol_above >= vol_below and upper + 1 < len(volume_at_price):
                upper += 1
                va_volume += vol_above
            elif lower - 1 >= 0:
                lower -= 1
                va_volume += vol_below
            else:
                break

        va_high = bins[min(upper + 1, len(bins) - 1)]
        va_low = bins[lower]

        return va_high, va_low

    def _find_volume_nodes(
        self,
        volume_at_price: np.ndarray,
        bins: np.ndarray,
        bin_size: float,
        total_volume: float
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Identifie les HVN et LVN.

        HVN (High Volume Nodes): niveaux avec volume significativement élevé
        LVN (Low Volume Nodes): niveaux avec volume significativement bas

        Args:
            volume_at_price: Volume à chaque niveau
            bins: Niveaux de prix
            bin_size: Taille d'un bin
            total_volume: Volume total

        Returns:
            Tuple (liste HVN, liste LVN)
        """
        avg_volume = np.mean(volume_at_price)
        std_volume = np.std(volume_at_price)

        hvn = []
        lvn = []

        for i in range(len(volume_at_price)):
            vol = volume_at_price[i]
            price = bins[i] + bin_size / 2
            pct = vol / total_volume * 100 if total_volume > 0 else 0

            # HVN: volume > moyenne + 1.5 * std
            if vol > avg_volume + 1.5 * std_volume:
                hvn.append({
                    'price': round(price, 2),
                    'volume': round(vol, 2),
                    'percentage': round(pct, 2)
                })

            # LVN: volume < moyenne - std (mais pas nul)
            elif vol > 0 and vol < avg_volume - std_volume:
                lvn.append({
                    'price': round(price, 2),
                    'volume': round(vol, 2),
                    'percentage': round(pct, 2)
                })

        # Garder les plus significatifs
        hvn = sorted(hvn, key=lambda x: x['volume'], reverse=True)[:5]
        lvn = sorted(lvn, key=lambda x: x['volume'])[:5]

        return hvn, lvn

    def get_trading_zones(
        self,
        df: pd.DataFrame,
        current_price: float
    ) -> Dict:
        """
        Identifie les zones de trading basées sur le Volume Profile.

        Args:
            df: DataFrame OHLCV
            current_price: Prix actuel

        Returns:
            Dict avec les zones de trading
        """
        profile = self.calculate_profile(df)

        if 'error' in profile:
            return profile

        poc = profile['poc']
        va_high = profile['value_area_high']
        va_low = profile['value_area_low']
        hvn = profile.get('hvn', [])
        lvn = profile.get('lvn', [])

        # Déterminer la position par rapport à la Value Area
        if current_price > va_high:
            position = 'above_va'
            bias = 'bullish'
            description = 'Prix au-dessus de la Value Area - momentum haussier'
        elif current_price < va_low:
            position = 'below_va'
            bias = 'bearish'
            description = 'Prix sous la Value Area - momentum baissier'
        else:
            position = 'inside_va'
            bias = 'neutral'
            description = 'Prix dans la Value Area - consolidation probable'

        # Identifier les supports et résistances basés sur le volume
        supports = []
        resistances = []

        for node in hvn:
            if node['price'] < current_price:
                supports.append(node['price'])
            else:
                resistances.append(node['price'])

        # Le POC est toujours un niveau clé
        if poc < current_price:
            supports.append(poc)
        else:
            resistances.append(poc)

        return {
            'current_price': round(current_price, 2),
            'poc': poc,
            'value_area': {
                'high': va_high,
                'low': va_low
            },
            'position': position,
            'bias': bias,
            'description': description,
            'volume_supports': sorted(set(supports), reverse=True)[:3],
            'volume_resistances': sorted(set(resistances))[:3],
            'hvn': hvn,
            'lvn': lvn
        }
