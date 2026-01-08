"""
Module de gestion des risques.

Implémente (selon TRADING_STRATEGIES_GUIDE.md):
- Position sizing (pourcentage fixe, Kelly Criterion, ATR-based)
- Stop-loss et take-profit
- Drawdown management
- Vérifications pré-trade
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class PositionSize:
    """Résultat du calcul de position sizing."""
    size: float              # Taille de la position en base currency
    size_quote: float        # Taille en quote currency
    risk_amount: float       # Montant risqué
    risk_percent: float      # Pourcentage du capital risqué
    kelly_full: float        # Kelly complet (pour info)
    kelly_used: float        # Kelly utilisé (quarter-kelly)


@dataclass
class StopTakeProfit:
    """Niveaux de stop-loss et take-profit."""
    stop_loss: float
    take_profit: float
    stop_distance: float
    take_distance: float
    risk_reward: float
    trailing_stop: Optional[float] = None


class RiskManager:
    """
    Gère tous les aspects du risque de trading.

    Règles absolues selon le Guide de Stratégies:
    - Max 1-2% de risque par trade
    - Max 3% de perte journalière
    - Max 6% d'exposition totale
    - Stop trading après 3 pertes consécutives
    """

    def __init__(self, config: dict):
        """
        Initialise le Risk Manager.

        Args:
            config: Configuration contenant risk_management
        """
        self.config = config.get('risk_management', {})

        # Limites de risque
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.01)
        self.max_risk_per_day = self.config.get('max_risk_per_day', 0.03)
        self.max_risk_total = self.config.get('max_risk_total', 0.06)
        self.max_open_positions = self.config.get('max_open_positions', 3)

        # Kelly Criterion
        self.kelly_fraction = self.config.get('kelly_fraction', 0.25)  # Quarter-Kelly

        # Stop Loss config
        self.sl_config = self.config.get('stop_loss', {})
        self.tp_config = self.config.get('take_profit', {})

        # Drawdown config
        self.dd_config = self.config.get('drawdown', {})

        # État du trading
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.pause_until: Optional[datetime] = None
        self.trade_history: list = []

    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        win_rate: float = 0.5,
        avg_win_loss_ratio: float = 2.0
    ) -> PositionSize:
        """
        Calcule la taille de position optimale.

        Méthodes utilisées:
        1. Pourcentage fixe (défaut)
        2. Kelly Criterion (optionnel)
        3. Ajustement ATR (si stop basé sur ATR)

        Formule: Position Size = (Capital × Risk%) / Stop Loss Distance

        Args:
            capital: Capital disponible
            entry_price: Prix d'entrée prévu
            stop_loss: Niveau de stop-loss
            win_rate: Taux de gain historique (pour Kelly)
            avg_win_loss_ratio: Ratio gain/perte moyen (pour Kelly)

        Returns:
            PositionSize avec tous les détails
        """
        # Distance du stop en valeur absolue et pourcentage
        stop_distance = abs(entry_price - stop_loss)
        stop_percent = stop_distance / entry_price

        if stop_percent == 0:
            logger.warning("Stop distance is zero, using default 2%")
            stop_percent = 0.02
            stop_distance = entry_price * stop_percent

        # Calcul Kelly Criterion
        # Kelly% = W - [(1-W) / R] où W = Win Rate, R = Risk/Reward
        kelly_full = win_rate - ((1 - win_rate) / avg_win_loss_ratio)
        kelly_full = max(0, kelly_full)  # Pas de position négative
        kelly_used = kelly_full * self.kelly_fraction  # Quarter-Kelly

        # Utiliser le minimum entre risk fixe et Kelly
        risk_percent = min(self.max_risk_per_trade, kelly_used) if kelly_used > 0 else self.max_risk_per_trade

        # Montant à risquer
        risk_amount = capital * risk_percent

        # Taille de position (en base currency)
        position_size = risk_amount / stop_distance
        position_size_quote = position_size * entry_price

        # Vérification que la position ne dépasse pas l'exposition max
        max_position_quote = capital * self.max_risk_total
        if position_size_quote > max_position_quote:
            position_size_quote = max_position_quote
            position_size = position_size_quote / entry_price
            risk_amount = position_size * stop_distance
            risk_percent = risk_amount / capital
            logger.info(f"Position réduite pour respecter l'exposition max: {position_size_quote:.2f}")

        return PositionSize(
            size=round(position_size, 8),
            size_quote=round(position_size_quote, 2),
            risk_amount=round(risk_amount, 2),
            risk_percent=round(risk_percent, 4),
            kelly_full=round(kelly_full, 4),
            kelly_used=round(kelly_used, 4)
        )

    def calculate_stop_take_profit(
        self,
        entry_price: float,
        direction: str,  # 'long' ou 'short'
        atr: float,
        style: str = 'swing'  # 'day', 'swing', 'position', 'volatile'
    ) -> StopTakeProfit:
        """
        Calcule les niveaux de stop-loss et take-profit basés sur ATR.

        Multiplicateurs ATR par style (selon Guide):
        - Day trading: 1.5-2.0×
        - Swing trading: 2.0-2.5×
        - Position trading: 2.5-3.0×
        - Haute volatilité: 3.0-4.0×

        Args:
            entry_price: Prix d'entrée
            direction: 'long' ou 'short'
            atr: Valeur ATR actuelle
            style: Style de trading

        Returns:
            StopTakeProfit avec tous les niveaux
        """
        # Sélection du multiplicateur ATR selon le style
        atr_multipliers = {
            'day': self.sl_config.get('atr_multiplier_day', 1.5),
            'swing': self.sl_config.get('atr_multiplier_swing', 2.0),
            'position': self.sl_config.get('atr_multiplier_position', 2.5),
            'volatile': self.sl_config.get('atr_multiplier_volatile', 3.0)
        }

        atr_mult = atr_multipliers.get(style, 2.0)
        stop_distance = atr * atr_mult

        # Risk/Reward ratio minimum
        min_rr = self.tp_config.get('min_risk_reward_ratio', 2.0)
        take_distance = stop_distance * min_rr

        # Calcul des niveaux selon la direction
        if direction == 'long':
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + take_distance
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - take_distance

        # Trailing stop (optionnel)
        trailing_stop = None
        if self.tp_config.get('trailing_stop', True):
            trailing_mult = self.tp_config.get('trailing_atr_multiplier', 1.0)
            trailing_stop = atr * trailing_mult

        return StopTakeProfit(
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            stop_distance=round(stop_distance, 2),
            take_distance=round(take_distance, 2),
            risk_reward=round(min_rr, 2),
            trailing_stop=round(trailing_stop, 2) if trailing_stop else None
        )

    def check_pre_trade_conditions(
        self,
        capital: float,
        current_positions: int,
        current_exposure: float,
        spread_percent: float
    ) -> Tuple[bool, str]:
        """
        Vérifie toutes les conditions pré-trade.

        Conditions (selon Guide):
        - daily_loss < MAX_DAILY_DRAWDOWN
        - consecutive_losses < 3
        - total_exposure < 6%
        - spread < 0.2%

        Args:
            capital: Capital actuel
            current_positions: Nombre de positions ouvertes
            current_exposure: Exposition actuelle en %
            spread_percent: Spread actuel en %

        Returns:
            Tuple (autorisé, raison)
        """
        # Vérifier si en pause
        if self.pause_until and datetime.now() < self.pause_until:
            remaining = (self.pause_until - datetime.now()).seconds // 60
            return False, f"En pause suite à pertes consécutives ({remaining} min restantes)"

        # Perte journalière
        daily_loss_limit = self.dd_config.get('daily_loss_limit', 0.03)
        if abs(self.daily_pnl) / capital > daily_loss_limit and self.daily_pnl < 0:
            return False, f"Limite de perte journalière atteinte ({daily_loss_limit*100}%)"

        # Pertes consécutives
        max_consecutive = self.dd_config.get('consecutive_loss_pause', 3)
        if self.consecutive_losses >= max_consecutive:
            pause_duration = self.dd_config.get('pause_duration_minutes', 15)
            self.pause_until = datetime.now() + timedelta(minutes=pause_duration)
            return False, f"{max_consecutive} pertes consécutives - pause de {pause_duration} min"

        # Nombre de positions
        if current_positions >= self.max_open_positions:
            return False, f"Nombre max de positions atteint ({self.max_open_positions})"

        # Exposition totale
        if current_exposure >= self.max_risk_total:
            return False, f"Exposition totale max atteinte ({self.max_risk_total*100}%)"

        # Spread
        max_spread = 0.002  # 0.2%
        if spread_percent > max_spread:
            return False, f"Spread trop élevé ({spread_percent*100:.2f}% > {max_spread*100}%)"

        return True, "OK"

    def update_trade_result(self, pnl: float, capital: float):
        """
        Met à jour les statistiques après un trade.

        Args:
            pnl: Profit/Loss du trade
            capital: Capital actuel
        """
        self.daily_pnl += pnl
        self.trade_history.append({
            'pnl': pnl,
            'timestamp': datetime.now(),
            'capital': capital
        })

        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        logger.info(f"Trade result: PnL={pnl:.2f}, Daily PnL={self.daily_pnl:.2f}, Consec losses={self.consecutive_losses}")

    def reset_daily_stats(self):
        """Réinitialise les statistiques journalières."""
        self.daily_pnl = 0.0
        logger.info("Daily stats reset")

    def get_scaling_out_levels(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str
    ) -> Dict:
        """
        Calcule les niveaux de scaling out progressif.

        Règle (selon Guide):
        - 33% à 1R, déplacer stop au breakeven
        - 33% à 2R, trailing sur le reste
        - 34% final avec trailing stop

        Args:
            entry_price: Prix d'entrée
            stop_loss: Niveau de stop
            direction: 'long' ou 'short'

        Returns:
            Dict avec les niveaux de scaling
        """
        risk = abs(entry_price - stop_loss)

        if direction == 'long':
            level_1 = entry_price + risk  # 1R
            level_2 = entry_price + (risk * 2)  # 2R
            level_3 = entry_price + (risk * 3)  # 3R
        else:
            level_1 = entry_price - risk
            level_2 = entry_price - (risk * 2)
            level_3 = entry_price - (risk * 3)

        scaling_config = self.tp_config.get('scaling_out', {})

        return {
            'level_1': {
                'price': round(level_1, 2),
                'percent': scaling_config.get('level_1_percent', 0.33),
                'r_multiple': 1,
                'action': 'Prendre 33%, stop au breakeven'
            },
            'level_2': {
                'price': round(level_2, 2),
                'percent': scaling_config.get('level_2_percent', 0.33),
                'r_multiple': 2,
                'action': 'Prendre 33%, activer trailing stop'
            },
            'level_3': {
                'price': round(level_3, 2),
                'percent': scaling_config.get('level_3_percent', 0.34),
                'r_multiple': 3,
                'action': 'Position finale avec trailing'
            }
        }

    def get_risk_summary(self, capital: float) -> Dict:
        """
        Retourne un résumé de l'état du risque.

        Args:
            capital: Capital actuel

        Returns:
            Dict avec le résumé
        """
        return {
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_pnl_percent': round(self.daily_pnl / capital * 100, 2) if capital > 0 else 0,
            'consecutive_losses': self.consecutive_losses,
            'is_paused': self.pause_until is not None and datetime.now() < self.pause_until,
            'pause_remaining_minutes': max(0, (self.pause_until - datetime.now()).seconds // 60) if self.pause_until and datetime.now() < self.pause_until else 0,
            'max_risk_per_trade': self.max_risk_per_trade,
            'max_daily_loss': self.dd_config.get('daily_loss_limit', 0.03),
            'max_drawdown': self.dd_config.get('max_drawdown', 0.15)
        }
