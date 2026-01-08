"""
Stratégie DCA intelligent avec triggers techniques.

Selon TRADING_STRATEGIES_GUIDE.md:
- BASE_ORDER = 100 USDT
- SAFETY_ORDERS = 5
- SCALE = 1.5 (multiplicateur de taille)
- Triggers RSI pour safety orders
- RSI_LEVELS = [29, 27.5, 26, 24, 22]
- PRICE_DROPS = [1.5%, 2.5%, 4%, 6%, 10%]
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DCAOrder:
    """Ordre DCA."""
    order_number: int
    size: float
    entry_price: float
    rsi_trigger: float
    price_drop_trigger: float
    filled: bool = False
    fill_price: float = None
    timestamp: datetime = None


class SmartDCAStrategy:
    """
    Stratégie DCA (Dollar Cost Averaging) intelligente.

    Cette stratégie accumule une position progressivement en utilisant
    des triggers techniques (RSI) et des niveaux de prix.
    """

    def __init__(self, config: dict):
        """
        Initialise la stratégie DCA Smart.

        Args:
            config: Configuration complète du bot
        """
        strategy_config = config.get('strategies', {}).get('dca_smart', {})
        self.enabled = strategy_config.get('enabled', False)
        self.base_order = strategy_config.get('base_order', 100)
        self.safety_orders = strategy_config.get('safety_orders', 5)
        self.scale_multiplier = strategy_config.get('scale_multiplier', 1.5)
        self.rsi_levels = strategy_config.get('rsi_levels', [29, 27.5, 26, 24, 22])
        self.price_drops = strategy_config.get('price_drops', [0.015, 0.025, 0.04, 0.06, 0.10])

        self.name = 'SmartDCA'
        self.orders: List[DCAOrder] = []
        self.base_entry_price = None
        self.total_invested = 0
        self.average_price = 0
        self.position_size = 0

    def initialize_dca(self, entry_price: float, symbol: str) -> List[Dict]:
        """
        Initialise une nouvelle série DCA.

        Args:
            entry_price: Prix d'entrée initial
            symbol: Symbole à trader

        Returns:
            Liste des ordres DCA planifiés
        """
        self.base_entry_price = entry_price
        self.orders = []
        self.total_invested = 0
        self.position_size = 0

        # Ordre de base
        base_order = DCAOrder(
            order_number=0,
            size=self.base_order,
            entry_price=entry_price,
            rsi_trigger=30,  # RSI standard pour le premier ordre
            price_drop_trigger=0,
            filled=True,
            fill_price=entry_price,
            timestamp=datetime.now()
        )
        self.orders.append(base_order)
        self._update_position(entry_price, self.base_order)

        # Safety orders
        planned_orders = [{
            'order_number': 0,
            'type': 'base',
            'size': self.base_order,
            'status': 'filled',
            'trigger_price': entry_price
        }]

        for i in range(self.safety_orders):
            order_size = self.base_order * (self.scale_multiplier ** (i + 1))
            trigger_price = entry_price * (1 - self.price_drops[i])
            rsi_trigger = self.rsi_levels[i] if i < len(self.rsi_levels) else 20

            safety_order = DCAOrder(
                order_number=i + 1,
                size=order_size,
                entry_price=trigger_price,
                rsi_trigger=rsi_trigger,
                price_drop_trigger=self.price_drops[i],
                filled=False
            )
            self.orders.append(safety_order)

            planned_orders.append({
                'order_number': i + 1,
                'type': 'safety',
                'size': round(order_size, 2),
                'status': 'pending',
                'trigger_price': round(trigger_price, 2),
                'rsi_trigger': rsi_trigger,
                'price_drop': f"{self.price_drops[i]*100:.1f}%"
            })

        logger.info(f"DCA initialisé pour {symbol} avec {self.safety_orders} safety orders")
        return planned_orders

    def check_safety_order_trigger(
        self,
        current_price: float,
        current_rsi: float
    ) -> Optional[Dict]:
        """
        Vérifie si un safety order doit être déclenché.

        Args:
            current_price: Prix actuel
            current_rsi: RSI actuel

        Returns:
            Dict avec l'ordre à exécuter si applicable
        """
        for order in self.orders:
            if order.filled:
                continue

            # Vérifier les conditions de déclenchement
            price_condition = current_price <= order.entry_price
            rsi_condition = current_rsi <= order.rsi_trigger

            if price_condition and rsi_condition:
                return {
                    'order_number': order.order_number,
                    'size': order.size,
                    'trigger_price': order.entry_price,
                    'actual_price': current_price,
                    'rsi': current_rsi,
                    'reason': f"Safety Order #{order.order_number}: Prix {current_price:.2f} <= {order.entry_price:.2f} et RSI {current_rsi:.1f} <= {order.rsi_trigger}"
                }

        return None

    def fill_order(self, order_number: int, fill_price: float) -> Dict:
        """
        Marque un ordre comme rempli et met à jour la position.

        Args:
            order_number: Numéro de l'ordre
            fill_price: Prix de remplissage

        Returns:
            Dict avec le nouveau statut de la position
        """
        for order in self.orders:
            if order.order_number == order_number and not order.filled:
                order.filled = True
                order.fill_price = fill_price
                order.timestamp = datetime.now()

                self._update_position(fill_price, order.size)

                return {
                    'order_number': order_number,
                    'fill_price': fill_price,
                    'order_size': order.size,
                    'total_invested': round(self.total_invested, 2),
                    'average_price': round(self.average_price, 2),
                    'position_size': round(self.position_size, 8),
                    'orders_filled': sum(1 for o in self.orders if o.filled),
                    'orders_remaining': sum(1 for o in self.orders if not o.filled)
                }

        return {'error': 'Order not found or already filled'}

    def _update_position(self, price: float, amount: float):
        """Met à jour les statistiques de position."""
        quantity = amount / price
        self.total_invested += amount
        self.position_size += quantity
        self.average_price = self.total_invested / self.position_size if self.position_size > 0 else 0

    def calculate_take_profit(self, target_profit_percent: float = 0.03) -> float:
        """
        Calcule le niveau de take-profit basé sur le prix moyen.

        Args:
            target_profit_percent: Pourcentage de profit cible (défaut 3%)

        Returns:
            Prix de take-profit
        """
        if self.average_price == 0:
            return 0

        return self.average_price * (1 + target_profit_percent)

    def get_position_status(self, current_price: float) -> Dict:
        """
        Retourne le statut actuel de la position DCA.

        Args:
            current_price: Prix actuel

        Returns:
            Dict avec toutes les statistiques
        """
        if self.position_size == 0:
            return {'status': 'no_position'}

        current_value = self.position_size * current_price
        unrealized_pnl = current_value - self.total_invested
        unrealized_pnl_percent = (unrealized_pnl / self.total_invested) * 100 if self.total_invested > 0 else 0

        # Distance au break-even
        distance_to_be = ((current_price / self.average_price) - 1) * 100 if self.average_price > 0 else 0

        return {
            'status': 'active',
            'base_entry_price': round(self.base_entry_price, 2) if self.base_entry_price else 0,
            'average_price': round(self.average_price, 2),
            'current_price': round(current_price, 2),
            'position_size': round(self.position_size, 8),
            'total_invested': round(self.total_invested, 2),
            'current_value': round(current_value, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'unrealized_pnl_percent': round(unrealized_pnl_percent, 2),
            'distance_to_breakeven': round(distance_to_be, 2),
            'orders_filled': sum(1 for o in self.orders if o.filled),
            'orders_remaining': sum(1 for o in self.orders if not o.filled),
            'take_profit_3pct': round(self.calculate_take_profit(0.03), 2),
            'take_profit_5pct': round(self.calculate_take_profit(0.05), 2)
        }

    def get_next_safety_order(self) -> Optional[Dict]:
        """
        Retourne le prochain safety order à déclencher.

        Returns:
            Dict avec les détails du prochain ordre
        """
        for order in self.orders:
            if not order.filled:
                return {
                    'order_number': order.order_number,
                    'trigger_price': round(order.entry_price, 2),
                    'rsi_trigger': order.rsi_trigger,
                    'size': round(order.size, 2),
                    'price_drop': f"{order.price_drop_trigger*100:.1f}%"
                }
        return None

    def should_close_position(
        self,
        current_price: float,
        target_profit: float = 0.03,
        stop_loss: float = 0.15
    ) -> Dict:
        """
        Détermine si la position doit être fermée.

        Args:
            current_price: Prix actuel
            target_profit: Objectif de profit (défaut 3%)
            stop_loss: Stop-loss (défaut 15%)

        Returns:
            Dict avec recommandation
        """
        if self.average_price == 0:
            return {'action': 'none', 'reason': 'No position'}

        pnl_percent = (current_price / self.average_price) - 1

        if pnl_percent >= target_profit:
            return {
                'action': 'take_profit',
                'reason': f"Objectif de profit atteint ({pnl_percent*100:.1f}% >= {target_profit*100:.1f}%)",
                'pnl_percent': round(pnl_percent * 100, 2),
                'close_price': current_price
            }

        if pnl_percent <= -stop_loss:
            return {
                'action': 'stop_loss',
                'reason': f"Stop-loss déclenché ({pnl_percent*100:.1f}% <= -{stop_loss*100:.1f}%)",
                'pnl_percent': round(pnl_percent * 100, 2),
                'close_price': current_price
            }

        return {
            'action': 'hold',
            'reason': 'Dans les limites',
            'pnl_percent': round(pnl_percent * 100, 2),
            'distance_to_tp': round((target_profit - pnl_percent) * 100, 2),
            'distance_to_sl': round((-stop_loss - pnl_percent) * 100, 2)
        }
