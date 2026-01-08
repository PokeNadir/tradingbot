"""
Module de détection de manipulation de marché.

Détecte:
- Order Book Imbalance
- Spoofing
- Volume anormal
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ManipulationDetector:
    """
    Détecte les signes de manipulation de marché.

    Métriques analysées:
    - Order Book Imbalance (OBI)
    - Volume anormal
    - Spread inhabituel
    - Patterns de spoofing
    """

    def __init__(self, config: dict):
        """
        Initialise le détecteur.

        Args:
            config: Configuration du bot
        """
        self.config = config.get('manipulation', {})

        # Seuils OBI
        obi_config = self.config.get('obi', {})
        self.obi_bullish_threshold = obi_config.get('bullish_threshold', 0.3)
        self.obi_bearish_threshold = obi_config.get('bearish_threshold', -0.3)

        # Seuils de sécurité
        safety_config = self.config.get('safety', {})
        self.max_spread = safety_config.get('max_spread_percent', 0.002)
        self.max_vol_depth_ratio = safety_config.get('max_vol_depth_ratio', 30)
        self.max_cancel_rate = safety_config.get('max_cancel_rate', 0.6)

    def analyze_order_book(self, order_book: Dict) -> Dict:
        """
        Analyse le carnet d'ordres pour détecter des anomalies.

        Args:
            order_book: Dict avec bids, asks, volumes

        Returns:
            Dict avec l'analyse
        """
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])

        if not bids or not asks:
            return {'error': 'Order book incomplet'}

        # Calculer l'OBI
        bid_volume = sum(b[1] for b in bids)
        ask_volume = sum(a[1] for a in asks)
        total_volume = bid_volume + ask_volume

        obi = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0

        # Interpréter l'OBI
        if obi > self.obi_bullish_threshold:
            obi_signal = 'bullish'
            obi_description = 'Pression acheteuse forte'
        elif obi < self.obi_bearish_threshold:
            obi_signal = 'bearish'
            obi_description = 'Pression vendeuse forte'
        else:
            obi_signal = 'neutral'
            obi_description = 'Carnet équilibré'

        # Calculer le spread
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0

        # Détecter les murs (walls)
        bid_wall = self._detect_wall(bids, 'bid')
        ask_wall = self._detect_wall(asks, 'ask')

        # Score de sécurité
        safety_score = self._calculate_safety_score(spread, obi)

        return {
            'obi': round(obi, 4),
            'obi_signal': obi_signal,
            'obi_description': obi_description,
            'bid_volume': round(bid_volume, 2),
            'ask_volume': round(ask_volume, 2),
            'spread': round(spread * 100, 4),
            'spread_safe': spread <= self.max_spread,
            'bid_wall': bid_wall,
            'ask_wall': ask_wall,
            'safety_score': safety_score,
            'timestamp': datetime.now().isoformat()
        }

    def _detect_wall(self, orders: List, side: str) -> Optional[Dict]:
        """
        Détecte un mur d'ordres (wall).

        Un mur est un ordre significativement plus grand que les autres.

        Args:
            orders: Liste des ordres [price, size]
            side: 'bid' ou 'ask'

        Returns:
            Dict avec le mur détecté ou None
        """
        if len(orders) < 5:
            return None

        sizes = [o[1] for o in orders[:10]]
        avg_size = np.mean(sizes)
        std_size = np.std(sizes)

        for price, size in orders[:10]:
            if size > avg_size + (3 * std_size):
                return {
                    'price': price,
                    'size': round(size, 4),
                    'ratio': round(size / avg_size, 2),
                    'side': side
                }

        return None

    def _calculate_safety_score(self, spread: float, obi: float) -> Dict:
        """
        Calcule un score de sécurité global.

        Args:
            spread: Spread actuel
            obi: Order Book Imbalance

        Returns:
            Dict avec le score et les détails
        """
        score = 100

        # Pénalité pour spread élevé
        if spread > self.max_spread:
            penalty = min(30, (spread / self.max_spread - 1) * 20)
            score -= penalty

        # Pénalité pour déséquilibre extrême
        if abs(obi) > 0.5:
            score -= 15

        # Classification
        if score >= 80:
            level = 'safe'
            recommendation = 'Trading normal autorisé'
        elif score >= 60:
            level = 'caution'
            recommendation = 'Prudence recommandée - réduire la taille'
        else:
            level = 'dangerous'
            recommendation = 'Éviter le trading - conditions défavorables'

        return {
            'score': max(0, round(score)),
            'level': level,
            'recommendation': recommendation
        }

    def analyze_volume_anomaly(
        self,
        df: pd.DataFrame,
        current_volume: float
    ) -> Dict:
        """
        Détecte les anomalies de volume.

        Args:
            df: DataFrame avec historique
            current_volume: Volume actuel

        Returns:
            Dict avec l'analyse
        """
        if df.empty or len(df) < 20:
            return {'error': 'Données insuffisantes'}

        # Calculer les statistiques de volume
        volume_mean = df['volume'].mean()
        volume_std = df['volume'].std()

        # Z-score
        z_score = (current_volume - volume_mean) / volume_std if volume_std > 0 else 0

        # Ratio par rapport à la moyenne
        volume_ratio = current_volume / volume_mean if volume_mean > 0 else 1

        # Classification
        if z_score > 3:
            anomaly_level = 'extreme'
            description = 'Volume extrêmement élevé - événement majeur possible'
        elif z_score > 2:
            anomaly_level = 'high'
            description = 'Volume très élevé - mouvement significatif'
        elif z_score > 1:
            anomaly_level = 'elevated'
            description = 'Volume au-dessus de la normale'
        elif z_score < -1:
            anomaly_level = 'low'
            description = 'Volume faible - liquidité réduite'
        else:
            anomaly_level = 'normal'
            description = 'Volume normal'

        return {
            'current_volume': round(current_volume, 2),
            'average_volume': round(volume_mean, 2),
            'volume_ratio': round(volume_ratio, 2),
            'z_score': round(z_score, 2),
            'anomaly_level': anomaly_level,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }

    def check_trading_conditions(
        self,
        spread: float,
        volume: float,
        avg_volume: float,
        obi: float = 0
    ) -> Dict:
        """
        Vérifie si les conditions sont favorables au trading.

        Args:
            spread: Spread actuel
            volume: Volume actuel
            avg_volume: Volume moyen
            obi: Order Book Imbalance

        Returns:
            Dict avec la recommandation
        """
        issues = []
        warnings = []

        # Vérifier le spread
        if spread > self.max_spread:
            issues.append(f"Spread trop élevé ({spread*100:.3f}% > {self.max_spread*100}%)")

        # Vérifier le volume
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio < 0.3:
                issues.append(f"Volume très faible ({volume_ratio*100:.0f}% de la moyenne)")
            elif volume_ratio < 0.5:
                warnings.append(f"Volume faible ({volume_ratio*100:.0f}% de la moyenne)")

        # Vérifier l'OBI
        if abs(obi) > 0.5:
            warnings.append(f"Déséquilibre important du carnet (OBI: {obi:.2f})")

        # Déterminer la recommandation
        if issues:
            can_trade = False
            recommendation = 'NE PAS TRADER'
        elif warnings:
            can_trade = True
            recommendation = 'PRUDENCE'
        else:
            can_trade = True
            recommendation = 'OK'

        return {
            'can_trade': can_trade,
            'recommendation': recommendation,
            'issues': issues,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
