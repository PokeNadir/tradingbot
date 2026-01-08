"""
Stratégie EMA Crossover avec confirmation ADX.

Selon TRADING_STRATEGIES_GUIDE.md:
- LONG: EMA_9 crosses above EMA_21 AND ADX > 25 AND RSI > 50
- SHORT: EMA_9 crosses below EMA_21 AND ADX > 25 AND RSI < 50
- STOP: 2× ATR
- TARGET: 1:2 risk-reward minimum
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from datetime import datetime
import logging

from backend.strategies.base_strategy import BaseStrategy, TradeProposal

logger = logging.getLogger(__name__)


class EMACrossoverStrategy(BaseStrategy):
    """
    Stratégie de croisement EMA avec confirmation de tendance.

    Cette stratégie suit la tendance en utilisant les croisements
    des moyennes mobiles exponentielles avec filtre ADX.
    """

    def __init__(self, config: dict):
        """
        Initialise la stratégie EMA Crossover.

        Args:
            config: Configuration complète du bot
        """
        strategy_config = config.get('strategies', {}).get('ema_crossover', {})
        super().__init__(strategy_config)

        self.fast_ema = strategy_config.get('fast_ema', 9)
        self.slow_ema = strategy_config.get('slow_ema', 21)
        self.adx_threshold = strategy_config.get('adx_threshold', 25)
        self.rsi_filter_long = strategy_config.get('rsi_filter_long', 50)
        self.rsi_filter_short = strategy_config.get('rsi_filter_short', 50)
        self.stop_atr_multiplier = strategy_config.get('stop_atr_multiplier', 2.0)
        self.min_risk_reward = strategy_config.get('min_risk_reward', 2.0)

    def analyze(self, df: pd.DataFrame, symbol: str) -> Optional[TradeProposal]:
        """
        Analyse les données pour détecter des croisements EMA.

        Args:
            df: DataFrame avec indicateurs (ema_*, adx, rsi, atr)
            symbol: Symbole à analyser

        Returns:
            TradeProposal si conditions remplies
        """
        if not self.enabled or df.empty or len(df) < 30:
            return None

        should_enter, direction, reasons = self.should_enter(df)

        if not should_enter:
            return None

        last = df.iloc[-1]
        entry_price = last['close']
        atr = last.get('atr', entry_price * 0.02)

        if pd.isna(atr) or atr == 0:
            atr = entry_price * 0.02

        # Calcul du stop-loss
        stop_loss = self.calculate_stop_loss(
            entry_price, direction, atr, self.stop_atr_multiplier
        )

        # Calcul du take-profit
        take_profit = self.calculate_take_profit(
            entry_price, stop_loss, direction, self.min_risk_reward
        )

        # Calcul du risk/reward
        if direction == 'long':
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit

        risk_reward = reward / risk if risk > 0 else 0

        # Calcul de la confiance
        confidence = self._calculate_confidence(df, direction)

        proposal = TradeProposal(
            symbol=symbol,
            direction=direction,
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            size=0,
            risk_reward=round(risk_reward, 2),
            confidence=confidence,
            strategy_name=self.name,
            reasons=reasons,
            timestamp=datetime.now()
        )

        if self.validate_trade(proposal):
            return proposal

        return None

    def should_enter(self, df: pd.DataFrame) -> tuple:
        """
        Vérifie les conditions d'entrée EMA Crossover.

        Conditions LONG:
        - EMA 9 croise au-dessus de EMA 21
        - ADX > 25 (marché en tendance)
        - RSI > 50 (momentum haussier)

        Conditions SHORT:
        - EMA 9 croise en dessous de EMA 21
        - ADX > 25
        - RSI < 50 (momentum baissier)
        """
        if len(df) < 3:
            return False, '', []

        last = df.iloc[-1]
        prev = df.iloc[-2]
        reasons = []

        # Récupérer les valeurs
        ema_fast = last.get('ema_9')
        ema_slow = last.get('ema_21')
        ema_fast_prev = prev.get('ema_9')
        ema_slow_prev = prev.get('ema_21')
        adx = last.get('adx')
        rsi = last.get('rsi')

        # Vérifier que les indicateurs sont disponibles
        if any(pd.isna(x) for x in [ema_fast, ema_slow, ema_fast_prev, ema_slow_prev, adx, rsi]):
            return False, '', []

        # Vérifier ADX (marché en tendance)
        if adx < self.adx_threshold:
            return False, '', []

        # Détecter le croisement LONG
        cross_up = (ema_fast > ema_slow) and (ema_fast_prev <= ema_slow_prev)
        # Détecter le croisement SHORT
        cross_down = (ema_fast < ema_slow) and (ema_fast_prev >= ema_slow_prev)

        # Conditions LONG
        if cross_up and rsi > self.rsi_filter_long:
            reasons.append(f"EMA {self.fast_ema} croise au-dessus de EMA {self.slow_ema}")
            reasons.append(f"ADX confirme tendance ({adx:.1f} > {self.adx_threshold})")
            reasons.append(f"RSI confirme momentum ({rsi:.1f} > {self.rsi_filter_long})")

            # Bonus: au-dessus de la SMA 200
            if last.get('above_sma200', False):
                reasons.append("Prix au-dessus de la SMA 200")

            return True, 'long', reasons

        # Conditions SHORT
        if cross_down and rsi < self.rsi_filter_short:
            reasons.append(f"EMA {self.fast_ema} croise en dessous de EMA {self.slow_ema}")
            reasons.append(f"ADX confirme tendance ({adx:.1f} > {self.adx_threshold})")
            reasons.append(f"RSI confirme momentum ({rsi:.1f} < {self.rsi_filter_short})")

            if not last.get('above_sma200', True):
                reasons.append("Prix sous la SMA 200")

            return True, 'short', reasons

        return False, '', []

    def _calculate_confidence(self, df: pd.DataFrame, direction: str) -> float:
        """
        Calcule la confiance du signal.

        Facteurs:
        - Force de l'ADX
        - Distance du RSI par rapport à 50
        - Alignement avec la SMA 200
        - Volume
        """
        last = df.iloc[-1]
        confidence = 0.5  # Base

        adx = last.get('adx', 25)
        rsi = last.get('rsi', 50)

        # ADX fort = plus de confiance
        if adx > 40:
            confidence += 0.15
        elif adx > 30:
            confidence += 0.1
        elif adx > 25:
            confidence += 0.05

        # RSI confirme la direction
        if direction == 'long':
            if rsi > 60:
                confidence += 0.1
            elif rsi > 55:
                confidence += 0.05
        else:
            if rsi < 40:
                confidence += 0.1
            elif rsi < 45:
                confidence += 0.05

        # Alignement SMA 200
        if direction == 'long' and last.get('above_sma200', False):
            confidence += 0.1
        elif direction == 'short' and not last.get('above_sma200', True):
            confidence += 0.1

        # Volume
        if last.get('high_volume', False):
            confidence += 0.1

        return min(1.0, max(0.0, confidence))
