"""
Stratégie Mean Reversion avec Bollinger Bands et RSI.

Selon TRADING_STRATEGIES_GUIDE.md:
- LONG: price < lower_band AND RSI < 30
- SHORT: price > upper_band AND RSI > 70
- TARGET: middle_band (SMA 20)
- STOP: 1.5× ATR au-delà de l'entrée
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from datetime import datetime
import logging

from backend.strategies.base_strategy import BaseStrategy, TradeProposal

logger = logging.getLogger(__name__)


class MeanReversionStrategy(BaseStrategy):
    """
    Stratégie de retour à la moyenne utilisant Bollinger Bands et RSI.

    Cette stratégie profite des mouvements excessifs pour anticiper
    un retour vers la moyenne (bande centrale).
    """

    def __init__(self, config: dict):
        """
        Initialise la stratégie Mean Reversion.

        Args:
            config: Configuration complète du bot
        """
        strategy_config = config.get('strategies', {}).get('mean_reversion', {})
        super().__init__(strategy_config)

        self.rsi_oversold = config.get('indicators', {}).get('rsi', {}).get('oversold', 30)
        self.rsi_overbought = config.get('indicators', {}).get('rsi', {}).get('overbought', 70)
        self.stop_atr_multiplier = strategy_config.get('stop_atr_multiplier', 1.5)
        self.min_risk_reward = strategy_config.get('min_risk_reward', 2.0)

    def analyze(self, df: pd.DataFrame, symbol: str) -> Optional[TradeProposal]:
        """
        Analyse les données pour détecter des opportunités de mean reversion.

        Args:
            df: DataFrame avec indicateurs (bb_*, rsi, atr)
            symbol: Symbole à analyser

        Returns:
            TradeProposal si conditions remplies
        """
        if not self.enabled or df.empty or len(df) < 20:
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

        # Target = bande centrale
        target = last.get('bb_middle', entry_price)
        if pd.isna(target):
            target = entry_price

        # Calcul du take-profit (target = bb_middle, mais respect du R:R minimum)
        if direction == 'long':
            potential_reward = target - entry_price
            risk = entry_price - stop_loss
            if risk > 0 and potential_reward / risk < self.min_risk_reward:
                take_profit = entry_price + (risk * self.min_risk_reward)
            else:
                take_profit = target
        else:
            potential_reward = entry_price - target
            risk = stop_loss - entry_price
            if risk > 0 and potential_reward / risk < self.min_risk_reward:
                take_profit = entry_price - (risk * self.min_risk_reward)
            else:
                take_profit = target

        # Calcul du risk/reward effectif
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
            size=0,  # Sera calculé par le risk manager
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
        Vérifie les conditions d'entrée Mean Reversion.

        Conditions LONG:
        - Prix sous la bande inférieure
        - RSI < 30 (survendu)

        Conditions SHORT:
        - Prix au-dessus de la bande supérieure
        - RSI > 70 (suracheté)
        """
        if len(df) < 2:
            return False, '', []

        last = df.iloc[-1]
        reasons = []

        # Récupérer les valeurs
        close = last['close']
        bb_lower = last.get('bb_lower')
        bb_upper = last.get('bb_upper')
        rsi = last.get('rsi')

        # Vérifier que les indicateurs sont disponibles
        if pd.isna(bb_lower) or pd.isna(bb_upper) or pd.isna(rsi):
            return False, '', []

        # Conditions LONG
        if close < bb_lower and rsi < self.rsi_oversold:
            reasons.append(f"Prix sous BB inférieure ({close:.2f} < {bb_lower:.2f})")
            reasons.append(f"RSI survendu ({rsi:.1f} < {self.rsi_oversold})")

            # Bonus: confirmer avec le volume
            if last.get('high_volume', False):
                reasons.append("Volume élevé confirme le signal")

            return True, 'long', reasons

        # Conditions SHORT
        if close > bb_upper and rsi > self.rsi_overbought:
            reasons.append(f"Prix au-dessus BB supérieure ({close:.2f} > {bb_upper:.2f})")
            reasons.append(f"RSI suracheté ({rsi:.1f} > {self.rsi_overbought})")

            if last.get('high_volume', False):
                reasons.append("Volume élevé confirme le signal")

            return True, 'short', reasons

        return False, '', []

    def _calculate_confidence(self, df: pd.DataFrame, direction: str) -> float:
        """
        Calcule la confiance du signal.

        Facteurs:
        - Distance par rapport à la bande
        - Niveau de RSI
        - Volume
        - Tendance récente
        """
        last = df.iloc[-1]
        confidence = 0.5  # Base

        close = last['close']
        bb_lower = last.get('bb_lower', close)
        bb_upper = last.get('bb_upper', close)
        bb_middle = last.get('bb_middle', close)
        rsi = last.get('rsi', 50)

        if direction == 'long':
            # Plus le prix est sous la bande, plus la confiance est haute
            if bb_middle != bb_lower:
                distance_ratio = (bb_middle - close) / (bb_middle - bb_lower)
                confidence += min(0.2, distance_ratio * 0.1)

            # RSI très survendu
            if rsi < 25:
                confidence += 0.15
            elif rsi < 30:
                confidence += 0.1

        else:  # short
            if bb_upper != bb_middle:
                distance_ratio = (close - bb_middle) / (bb_upper - bb_middle)
                confidence += min(0.2, distance_ratio * 0.1)

            if rsi > 75:
                confidence += 0.15
            elif rsi > 70:
                confidence += 0.1

        # Volume bonus
        if last.get('high_volume', False):
            confidence += 0.1

        # Squeeze bonus (breakout probable)
        if last.get('bb_squeeze', False):
            confidence += 0.05

        return min(1.0, max(0.0, confidence))
