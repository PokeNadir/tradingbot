"""
Stratégie Breakout avec filtre de volume.

Selon TRADING_STRATEGIES_GUIDE.md:
- resistance = rolling_max(high, 20)
- support = rolling_min(low, 20)
- LONG: close > resistance AND volume > avg_volume × 1.5
- SHORT: close < support AND volume > avg_volume × 1.5
- CONFIRM: ADX rising toward 25-40 zone
- STOP: 1.5× ATR
- TARGET: range_height projeté depuis breakout
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from datetime import datetime
import logging

from backend.strategies.base_strategy import BaseStrategy, TradeProposal

logger = logging.getLogger(__name__)


class BreakoutStrategy(BaseStrategy):
    """
    Stratégie de breakout sur cassure de niveaux avec confirmation volume.

    Cette stratégie identifie les cassures de supports/résistances
    confirmées par le volume et le momentum.
    """

    def __init__(self, config: dict):
        """
        Initialise la stratégie Breakout.

        Args:
            config: Configuration complète du bot
        """
        strategy_config = config.get('strategies', {}).get('breakout', {})
        super().__init__(strategy_config)

        self.lookback_period = strategy_config.get('lookback_period', 20)
        self.volume_multiplier = strategy_config.get('volume_multiplier', 1.5)
        self.adx_confirmation = strategy_config.get('adx_confirmation', True)
        self.stop_atr_multiplier = strategy_config.get('stop_atr_multiplier', 1.5)
        self.min_risk_reward = strategy_config.get('min_risk_reward', 2.0)

    def analyze(self, df: pd.DataFrame, symbol: str) -> Optional[TradeProposal]:
        """
        Analyse les données pour détecter des breakouts.

        Args:
            df: DataFrame avec indicateurs
            symbol: Symbole à analyser

        Returns:
            TradeProposal si conditions remplies
        """
        if not self.enabled or df.empty or len(df) < self.lookback_period + 5:
            return None

        # Calculer les niveaux de support/résistance
        df = self._calculate_levels(df)

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

        # Target basé sur la hauteur du range cassé
        range_height = last.get('resistance', entry_price) - last.get('support', entry_price)
        if range_height <= 0:
            range_height = atr * 4

        if direction == 'long':
            take_profit = entry_price + range_height
        else:
            take_profit = entry_price - range_height

        # Vérifier le R:R minimum
        if direction == 'long':
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit

        if risk > 0 and reward / risk < self.min_risk_reward:
            take_profit = self.calculate_take_profit(
                entry_price, stop_loss, direction, self.min_risk_reward
            )
            reward = risk * self.min_risk_reward

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

    def _calculate_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule les niveaux de support et résistance.

        Args:
            df: DataFrame OHLCV

        Returns:
            DataFrame avec colonnes resistance et support
        """
        df = df.copy()
        df['resistance'] = df['high'].rolling(self.lookback_period).max()
        df['support'] = df['low'].rolling(self.lookback_period).min()
        return df

    def should_enter(self, df: pd.DataFrame) -> tuple:
        """
        Vérifie les conditions d'entrée Breakout.

        Conditions LONG:
        - Close > résistance (rolling max)
        - Volume > volume moyen × 1.5
        - ADX en hausse vers 25-40 (optionnel)

        Conditions SHORT:
        - Close < support (rolling min)
        - Volume > volume moyen × 1.5
        - ADX en hausse vers 25-40 (optionnel)
        """
        if len(df) < 3:
            return False, '', []

        last = df.iloc[-1]
        prev = df.iloc[-2]
        reasons = []

        # Récupérer les valeurs
        close = last['close']
        resistance = last.get('resistance')
        support = last.get('support')
        volume = last.get('volume', 0)
        volume_sma = last.get('volume_sma', 1)
        adx = last.get('adx')

        # Vérifier que les indicateurs sont disponibles
        if pd.isna(resistance) or pd.isna(support):
            return False, '', []

        # Vérification du volume
        volume_valid = volume > (volume_sma * self.volume_multiplier) if volume_sma > 0 else False

        if not volume_valid:
            return False, '', []

        # Vérification ADX (optionnelle)
        if self.adx_confirmation and pd.notna(adx):
            prev_adx = prev.get('adx', 0)
            adx_rising = adx > prev_adx
            adx_valid = adx_rising or adx > 25
        else:
            adx_valid = True

        # Breakout LONG
        prev_close = prev.get('close', close)
        if close > resistance and prev_close <= resistance:
            reasons.append(f"Cassure de résistance ({close:.2f} > {resistance:.2f})")
            reasons.append(f"Volume confirme ({volume/volume_sma:.1f}× la moyenne)")

            if self.adx_confirmation and pd.notna(adx):
                if adx > 25:
                    reasons.append(f"ADX confirme tendance ({adx:.1f})")
                elif adx_valid:
                    reasons.append("ADX en hausse")

            if adx_valid:
                return True, 'long', reasons

        # Breakout SHORT
        if close < support and prev_close >= support:
            reasons.append(f"Cassure de support ({close:.2f} < {support:.2f})")
            reasons.append(f"Volume confirme ({volume/volume_sma:.1f}× la moyenne)")

            if self.adx_confirmation and pd.notna(adx):
                if adx > 25:
                    reasons.append(f"ADX confirme tendance ({adx:.1f})")
                elif adx_valid:
                    reasons.append("ADX en hausse")

            if adx_valid:
                return True, 'short', reasons

        return False, '', []

    def _calculate_confidence(self, df: pd.DataFrame, direction: str) -> float:
        """
        Calcule la confiance du signal breakout.

        Facteurs:
        - Intensité du volume
        - Force de l'ADX
        - Taille de la bougie de cassure
        - Pas de faux breakouts récents
        """
        last = df.iloc[-1]
        confidence = 0.5  # Base

        # Volume intensity
        volume = last.get('volume', 0)
        volume_sma = last.get('volume_sma', 1)
        if volume_sma > 0:
            volume_ratio = volume / volume_sma
            if volume_ratio > 2.5:
                confidence += 0.15
            elif volume_ratio > 2.0:
                confidence += 0.1
            elif volume_ratio > 1.5:
                confidence += 0.05

        # ADX strength
        adx = last.get('adx', 20)
        if adx > 35:
            confidence += 0.15
        elif adx > 25:
            confidence += 0.1

        # Candle body size (momentum)
        close = last['close']
        open_price = last['open']
        high = last['high']
        low = last['low']

        body = abs(close - open_price)
        total_range = high - low

        if total_range > 0:
            body_ratio = body / total_range
            if body_ratio > 0.7:  # Strong momentum candle
                confidence += 0.1
            elif body_ratio > 0.5:
                confidence += 0.05

        # Alignment with trend
        if direction == 'long' and close > open_price:
            confidence += 0.05
        elif direction == 'short' and close < open_price:
            confidence += 0.05

        return min(1.0, max(0.0, confidence))
