"""
Stratégie Grid Trading pour marchés en range.

Selon TRADING_STRATEGIES_GUIDE.md:
- Placer buy orders sous le prix actuel à chaque niveau
- Placer sell orders au-dessus
- Quand buy remplit → placer sell au niveau supérieur
- Stop-loss global sous le niveau le plus bas
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class GridLevel:
    """Niveau de la grille."""
    price: float
    order_type: str  # 'buy' ou 'sell'
    filled: bool = False
    order_id: str = None


class GridTradingStrategy:
    """
    Stratégie de Grid Trading pour les marchés ranging.

    Cette stratégie place des ordres d'achat et de vente à intervalles
    réguliers dans un range défini. Idéale pour les marchés sans tendance.
    """

    def __init__(self, config: dict):
        """
        Initialise la stratégie Grid Trading.

        Args:
            config: Configuration complète du bot
        """
        strategy_config = config.get('strategies', {}).get('grid_trading', {})
        self.enabled = strategy_config.get('enabled', False)
        self.num_grids = strategy_config.get('num_grids', 20)
        self.grid_type = strategy_config.get('grid_type', 'geometric')

        self.name = 'GridTrading'
        self.grid_levels: List[GridLevel] = []
        self.lower_price = None
        self.upper_price = None
        self.investment_per_grid = 0

    def setup_grid(
        self,
        lower_price: float,
        upper_price: float,
        total_investment: float,
        current_price: float
    ) -> List[Dict]:
        """
        Configure la grille de trading.

        Args:
            lower_price: Prix minimum du range
            upper_price: Prix maximum du range
            total_investment: Montant total à investir
            current_price: Prix actuel

        Returns:
            Liste des ordres à placer
        """
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.investment_per_grid = total_investment / self.num_grids
        self.grid_levels = []

        # Calculer les niveaux selon le type de grille
        if self.grid_type == 'geometric':
            levels = self._calculate_geometric_levels()
        else:
            levels = self._calculate_arithmetic_levels()

        # Créer les niveaux de grille
        orders = []
        for i, price in enumerate(levels):
            if price < current_price:
                # Niveaux sous le prix actuel → ordres d'achat
                order_type = 'buy'
            else:
                # Niveaux au-dessus du prix actuel → ordres de vente
                order_type = 'sell'

            level = GridLevel(
                price=round(price, 2),
                order_type=order_type
            )
            self.grid_levels.append(level)

            orders.append({
                'price': level.price,
                'type': order_type,
                'size': self.investment_per_grid / price if order_type == 'buy' else 0,
                'level_index': i
            })

        logger.info(f"Grid configurée: {len(orders)} niveaux de {lower_price} à {upper_price}")
        return orders

    def _calculate_geometric_levels(self) -> List[float]:
        """
        Calcule les niveaux géométriques (spacing proportionnel).

        Formule: ratio = (upper / lower) ^ (1 / num_grids)
        levels = [lower × ratio^i for i in range(num_grids + 1)]
        """
        ratio = (self.upper_price / self.lower_price) ** (1 / self.num_grids)
        levels = [self.lower_price * (ratio ** i) for i in range(self.num_grids + 1)]
        return levels

    def _calculate_arithmetic_levels(self) -> List[float]:
        """
        Calcule les niveaux arithmétiques (spacing constant).
        """
        step = (self.upper_price - self.lower_price) / self.num_grids
        levels = [self.lower_price + (step * i) for i in range(self.num_grids + 1)]
        return levels

    def process_fill(self, filled_level: int, fill_price: float) -> Optional[Dict]:
        """
        Traite un ordre rempli et génère l'ordre opposé.

        Args:
            filled_level: Index du niveau rempli
            fill_price: Prix de remplissage

        Returns:
            Nouvel ordre à placer si applicable
        """
        if filled_level >= len(self.grid_levels):
            return None

        level = self.grid_levels[filled_level]
        level.filled = True

        # Si c'était un buy, placer un sell au niveau supérieur
        if level.order_type == 'buy' and filled_level < len(self.grid_levels) - 1:
            next_level = self.grid_levels[filled_level + 1]
            return {
                'price': next_level.price,
                'type': 'sell',
                'size': self.investment_per_grid / fill_price,
                'level_index': filled_level + 1
            }

        # Si c'était un sell, placer un buy au niveau inférieur
        elif level.order_type == 'sell' and filled_level > 0:
            prev_level = self.grid_levels[filled_level - 1]
            return {
                'price': prev_level.price,
                'type': 'buy',
                'size': self.investment_per_grid / prev_level.price,
                'level_index': filled_level - 1
            }

        return None

    def check_grid_exit(self, current_price: float) -> Dict:
        """
        Vérifie si le prix sort de la grille.

        Args:
            current_price: Prix actuel

        Returns:
            Dict avec action recommandée
        """
        if current_price < self.lower_price:
            return {
                'action': 'exit',
                'reason': f"Prix ({current_price}) sous le bas de grille ({self.lower_price})",
                'recommendation': 'Fermer toutes les positions et reconfigurer la grille plus bas'
            }

        if current_price > self.upper_price:
            return {
                'action': 'exit',
                'reason': f"Prix ({current_price}) au-dessus du haut de grille ({self.upper_price})",
                'recommendation': 'Fermer toutes les positions et reconfigurer la grille plus haut'
            }

        return {
            'action': 'hold',
            'reason': 'Prix dans la grille',
            'current_price': current_price,
            'range': [self.lower_price, self.upper_price]
        }

    def get_grid_status(self) -> Dict:
        """
        Retourne le statut actuel de la grille.

        Returns:
            Dict avec statistiques de la grille
        """
        if not self.grid_levels:
            return {'status': 'not_configured'}

        filled_buys = sum(1 for l in self.grid_levels if l.filled and l.order_type == 'buy')
        filled_sells = sum(1 for l in self.grid_levels if l.filled and l.order_type == 'sell')
        total_filled = filled_buys + filled_sells

        return {
            'status': 'active' if self.enabled else 'inactive',
            'lower_price': self.lower_price,
            'upper_price': self.upper_price,
            'num_grids': self.num_grids,
            'grid_type': self.grid_type,
            'total_levels': len(self.grid_levels),
            'filled_buys': filled_buys,
            'filled_sells': filled_sells,
            'total_filled': total_filled,
            'investment_per_grid': self.investment_per_grid
        }

    def estimate_profit_potential(self, current_price: float) -> Dict:
        """
        Estime le potentiel de profit de la grille.

        Args:
            current_price: Prix actuel

        Returns:
            Dict avec estimations
        """
        if not self.grid_levels or len(self.grid_levels) < 2:
            return {'error': 'Grid not configured'}

        # Profit par grid cycle (buy low, sell high)
        avg_grid_size = (self.upper_price - self.lower_price) / self.num_grids
        profit_per_cycle = (avg_grid_size / current_price) * self.investment_per_grid

        # Estimation du nombre de cycles par période (dépend de la volatilité)
        # Hypothèse: 1-3 cycles par jour en marché ranging

        return {
            'avg_grid_size': round(avg_grid_size, 2),
            'avg_grid_percent': round(avg_grid_size / current_price * 100, 2),
            'profit_per_cycle': round(profit_per_cycle, 2),
            'estimated_daily_profit_low': round(profit_per_cycle * 1, 2),
            'estimated_daily_profit_high': round(profit_per_cycle * 3, 2),
            'investment_per_grid': round(self.investment_per_grid, 2)
        }
