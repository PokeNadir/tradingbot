"""
Module de génération de signaux de trading.

Combine tous les indicateurs pour générer des signaux de trading cohérents.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from backend.indicators.technical import TechnicalIndicators
from backend.indicators.patterns import PatternDetector, CandlePattern
from backend.indicators.divergences import DivergenceDetector, Divergence
from backend.indicators.smc import SmartMoneyConcepts

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Signal de trading généré."""
    symbol: str
    type: str  # 'LONG' ou 'SHORT'
    strength: float  # 0.0 à 1.0
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    reasons: List[str]
    indicators: Dict
    timestamp: datetime
    strategy: str = 'combined'


class SignalGenerator:
    """
    Génère des signaux de trading en combinant plusieurs indicateurs.

    Logique d'entrée universelle selon le Guide de Stratégies:
    1. Filtre de tendance HTF (price > EMA_200)
    2. Signal technique (RSI, MACD)
    3. Confirmation volume
    4. Price action (patterns)
    5. Market regime (ADX)
    """

    def __init__(
        self,
        config: dict,
        technical: TechnicalIndicators,
        patterns: PatternDetector,
        divergences: DivergenceDetector,
        smc: SmartMoneyConcepts
    ):
        """
        Initialise le générateur de signaux.

        Args:
            config: Configuration du bot
            technical: Module d'indicateurs techniques
            patterns: Détecteur de patterns
            divergences: Détecteur de divergences
            smc: Analyseur Smart Money Concepts
        """
        self.config = config
        self.technical = technical
        self.patterns = patterns
        self.divergences = divergences
        self.smc = smc

        # Paramètres de signaux
        self.min_strength = 0.6
        self.min_rr_ratio = config.get('risk_management', {}).get('take_profit', {}).get('min_risk_reward_ratio', 2.0)

    def generate_all_signals(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
        """
        Génère tous les signaux pour un symbole.

        Args:
            df: DataFrame OHLCV
            symbol: Symbole de trading

        Returns:
            Liste des signaux détectés
        """
        if df.empty or len(df) < 50:
            return []

        # Calculer tous les indicateurs
        df = self.technical.calculate_all(df)
        df = self.smc.analyze(df)

        # Détecter patterns et divergences
        detected_patterns = self.patterns.detect_all(df)
        detected_divergences = self.divergences.detect_all(df)

        signals = []

        # Générer signal long
        long_signal = self._check_long_signal(df, symbol, detected_patterns, detected_divergences)
        if long_signal:
            signals.append(self._signal_to_dict(long_signal))

        # Générer signal short
        short_signal = self._check_short_signal(df, symbol, detected_patterns, detected_divergences)
        if short_signal:
            signals.append(self._signal_to_dict(short_signal))

        return signals

    def _check_long_signal(
        self,
        df: pd.DataFrame,
        symbol: str,
        patterns: List[CandlePattern],
        divergences: List[Divergence]
    ) -> Optional[TradingSignal]:
        """
        Vérifie les conditions pour un signal long.

        Conditions:
        1. Trend filter: price > SMA 200 (ou neutre)
        2. RSI: survendu ou crossing up
        3. MACD: crossing up ou histogram positif
        4. Volume: above average
        5. Pattern: bullish pattern
        """
        last = df.iloc[-1]
        reasons = []
        score = 0
        max_score = 10

        # 1. Trend filter (2 points)
        if pd.notna(last.get('sma_200')) and last['close'] > last['sma_200']:
            score += 2
            reasons.append("Prix au-dessus de la SMA 200 (tendance haussière)")
        elif pd.notna(last.get('sma_200')) and last['close'] < last['sma_200']:
            score -= 1  # Pénalité légère

        # 2. RSI conditions (2 points)
        rsi = last.get('rsi', 50)
        if pd.notna(rsi):
            if rsi < 30:
                score += 2
                reasons.append(f"RSI survendu ({rsi:.1f})")
            elif rsi < 40:
                score += 1
                reasons.append(f"RSI bas ({rsi:.1f})")
            elif rsi > 70:
                score -= 2  # Suracheté, pas bon pour long

        # 3. MACD conditions (2 points)
        macd = last.get('macd', 0)
        macd_signal = last.get('macd_signal', 0)
        macd_cross = last.get('macd_cross_up', False)

        if pd.notna(macd) and pd.notna(macd_signal):
            if macd_cross:
                score += 2
                reasons.append("MACD croisement haussier")
            elif macd > macd_signal and macd < 0:
                score += 1
                reasons.append("MACD haussier sous zéro")

        # 4. Volume confirmation (1 point)
        if last.get('high_volume', False):
            score += 1
            reasons.append("Volume élevé")

        # 5. Bollinger Bands (1 point)
        if last.get('below_bb_lower', False):
            score += 1
            reasons.append("Prix sous la bande de Bollinger inférieure")

        # 6. Patterns (2 points)
        bullish_patterns = [p for p in patterns if p.type == 'bullish']
        if bullish_patterns:
            best_pattern = max(bullish_patterns, key=lambda p: p.confidence)
            score += min(2, int(best_pattern.confidence * 2))
            reasons.append(f"Pattern: {best_pattern.name}")

        # 7. Divergences (bonus)
        bullish_divs = [d for d in divergences if 'bullish' in d.type]
        if bullish_divs:
            score += 1
            reasons.append(f"Divergence haussière détectée")

        # 8. SMC conditions (bonus)
        smc_summary = self.smc.get_structure_summary()
        if smc_summary.get('active_bullish_ob', 0) > 0:
            score += 0.5
            reasons.append("Order Block haussier actif")
        if smc_summary.get('active_bullish_fvg', 0) > 0:
            score += 0.5
            reasons.append("Fair Value Gap haussier")

        # Calcul de la force du signal
        strength = min(1.0, max(0.0, score / max_score))

        if strength < self.min_strength:
            return None

        # Calcul des niveaux
        entry_price = last['close']
        atr = last.get('atr', entry_price * 0.02)

        if pd.isna(atr) or atr == 0:
            atr = entry_price * 0.02

        stop_loss = entry_price - (atr * 2.0)
        take_profit = entry_price + (atr * 2.0 * self.min_rr_ratio)
        risk_reward = self.min_rr_ratio

        return TradingSignal(
            symbol=symbol,
            type='LONG',
            strength=strength,
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            risk_reward=risk_reward,
            reasons=reasons,
            indicators=self.technical.get_current_values(df),
            timestamp=datetime.now(),
            strategy='combined'
        )

    def _check_short_signal(
        self,
        df: pd.DataFrame,
        symbol: str,
        patterns: List[CandlePattern],
        divergences: List[Divergence]
    ) -> Optional[TradingSignal]:
        """
        Vérifie les conditions pour un signal short.
        """
        last = df.iloc[-1]
        reasons = []
        score = 0
        max_score = 10

        # 1. Trend filter (2 points)
        if pd.notna(last.get('sma_200')) and last['close'] < last['sma_200']:
            score += 2
            reasons.append("Prix sous la SMA 200 (tendance baissière)")
        elif pd.notna(last.get('sma_200')) and last['close'] > last['sma_200']:
            score -= 1

        # 2. RSI conditions (2 points)
        rsi = last.get('rsi', 50)
        if pd.notna(rsi):
            if rsi > 70:
                score += 2
                reasons.append(f"RSI suracheté ({rsi:.1f})")
            elif rsi > 60:
                score += 1
                reasons.append(f"RSI élevé ({rsi:.1f})")
            elif rsi < 30:
                score -= 2

        # 3. MACD conditions (2 points)
        macd = last.get('macd', 0)
        macd_signal = last.get('macd_signal', 0)
        macd_cross = last.get('macd_cross_down', False)

        if pd.notna(macd) and pd.notna(macd_signal):
            if macd_cross:
                score += 2
                reasons.append("MACD croisement baissier")
            elif macd < macd_signal and macd > 0:
                score += 1
                reasons.append("MACD baissier au-dessus de zéro")

        # 4. Volume confirmation (1 point)
        if last.get('high_volume', False):
            score += 1
            reasons.append("Volume élevé")

        # 5. Bollinger Bands (1 point)
        if last.get('above_bb_upper', False):
            score += 1
            reasons.append("Prix au-dessus de la bande de Bollinger supérieure")

        # 6. Patterns (2 points)
        bearish_patterns = [p for p in patterns if p.type == 'bearish']
        if bearish_patterns:
            best_pattern = max(bearish_patterns, key=lambda p: p.confidence)
            score += min(2, int(best_pattern.confidence * 2))
            reasons.append(f"Pattern: {best_pattern.name}")

        # 7. Divergences (bonus)
        bearish_divs = [d for d in divergences if 'bearish' in d.type]
        if bearish_divs:
            score += 1
            reasons.append(f"Divergence baissière détectée")

        # 8. SMC conditions (bonus)
        smc_summary = self.smc.get_structure_summary()
        if smc_summary.get('active_bearish_ob', 0) > 0:
            score += 0.5
            reasons.append("Order Block baissier actif")
        if smc_summary.get('active_bearish_fvg', 0) > 0:
            score += 0.5
            reasons.append("Fair Value Gap baissier")

        # Calcul de la force du signal
        strength = min(1.0, max(0.0, score / max_score))

        if strength < self.min_strength:
            return None

        # Calcul des niveaux
        entry_price = last['close']
        atr = last.get('atr', entry_price * 0.02)

        if pd.isna(atr) or atr == 0:
            atr = entry_price * 0.02

        stop_loss = entry_price + (atr * 2.0)
        take_profit = entry_price - (atr * 2.0 * self.min_rr_ratio)
        risk_reward = self.min_rr_ratio

        return TradingSignal(
            symbol=symbol,
            type='SHORT',
            strength=strength,
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            risk_reward=risk_reward,
            reasons=reasons,
            indicators=self.technical.get_current_values(df),
            timestamp=datetime.now(),
            strategy='combined'
        )

    def _signal_to_dict(self, signal: TradingSignal) -> Dict:
        """Convertit un signal en dictionnaire."""
        return {
            'symbol': signal.symbol,
            'type': signal.type,
            'strength': round(signal.strength, 2),
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'risk_reward': signal.risk_reward,
            'reasons': signal.reasons,
            'indicators': signal.indicators,
            'timestamp': signal.timestamp.isoformat(),
            'strategy': signal.strategy
        }

    def get_market_analysis(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Retourne une analyse complète du marché.

        Args:
            df: DataFrame avec données
            symbol: Symbole

        Returns:
            Dict avec l'analyse complète
        """
        if df.empty:
            return {'error': 'No data available'}

        df = self.technical.calculate_all(df)
        df = self.smc.analyze(df)

        indicators = self.technical.get_current_values(df)
        patterns = self.patterns.get_patterns_summary(df)
        divergences = self.divergences.get_divergences_summary(df)
        smc = self.smc.get_structure_summary()

        # Déterminer le biais global
        bullish_count = 0
        bearish_count = 0

        if indicators.get('trend_bias', 0) > 0:
            bullish_count += 1
        elif indicators.get('trend_bias', 0) < 0:
            bearish_count += 1

        if indicators.get('rsi', 50) < 40:
            bullish_count += 1
        elif indicators.get('rsi', 50) > 60:
            bearish_count += 1

        if patterns.get('bullish_count', 0) > 0:
            bullish_count += 1
        if patterns.get('bearish_count', 0) > 0:
            bearish_count += 1

        if divergences.get('bullish_count', 0) > 0:
            bullish_count += 1
        if divergences.get('bearish_count', 0) > 0:
            bearish_count += 1

        if bullish_count > bearish_count:
            bias = 'BULLISH'
        elif bearish_count > bullish_count:
            bias = 'BEARISH'
        else:
            bias = 'NEUTRAL'

        return {
            'symbol': symbol,
            'bias': bias,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'indicators': indicators,
            'patterns': patterns,
            'divergences': divergences,
            'smc': smc,
            'timestamp': datetime.now().isoformat()
        }
