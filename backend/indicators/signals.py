"""
Module de génération de signaux de trading.

Combine tous les indicateurs pour générer des signaux de trading cohérents.
Système de scoring selon logique.md (0-100 points).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from backend.indicators.technical import TechnicalIndicators
from backend.indicators.patterns import PatternDetector, CandlePattern
from backend.indicators.divergences import DivergenceDetector, Divergence
from backend.indicators.smc import SmartMoneyConcepts

logger = logging.getLogger(__name__)


class TradingState(Enum):
    """État de la machine d'état de trading selon logique.md."""
    SCANNING = "SCANNING"      # Recherche de signaux
    ARMED = "ARMED"            # Signal détecté, en attente de confirmation
    IN_POSITION = "IN_POSITION"  # En position
    COOLDOWN = "COOLDOWN"      # Période de pause après sortie


@dataclass
class TradingSignal:
    """Signal de trading généré."""
    symbol: str
    type: str  # 'LONG' ou 'SHORT'
    strength: float  # 0.0 à 1.0 (basé sur score 0-100)
    strength_score: int  # Score brut 0-100
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    reasons: List[str]
    indicators: Dict
    timestamp: datetime
    strategy: str = 'combined'
    confirmations: Dict = field(default_factory=dict)


class SignalGenerator:
    """
    Génère des signaux de trading en combinant plusieurs indicateurs.

    Système de scoring selon logique.md:
    - trend_aligned: +25 points
    - rsi_confirms: +15 points
    - macd_confirms: +10 points
    - volume_above_avg: +20 points
    - htf_aligned: +20 points
    - adx bonus: jusqu'à +10 points

    Triple Confirmation Entry (logique.md):
    1. close > ema_200 (filtre tendance)
    2. rsi > 30 AND rsi < 70 (RSI zone neutre)
    3. macd_line > signal_line (MACD haussier)
    4. adx > 25 (tendance établie)
    5. volume > avg_volume × 1.2 (confirmation volume)
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

        # Paramètres de signaux selon logique.md
        self.min_strength_score = 50  # Score minimum pour signal (sur 100)
        self.min_rr_ratio = config.get('risk_management', {}).get('take_profit', {}).get('min_risk_reward_ratio', 2.0)

        # Machine d'état selon logique.md
        self.states: Dict[str, TradingState] = {}  # État par symbole
        self.cooldown_bars: Dict[str, int] = {}  # Bars de cooldown par symbole
        self.armed_signals: Dict[str, TradingSignal] = {}  # Signaux en attente de confirmation
        self.position_info: Dict[str, Dict] = {}  # Info sur positions actives

        # Paramètres de la machine d'état
        self.confirmation_bars = 2  # Bougies pour confirmer un signal ARMED
        self.cooldown_duration = 5  # Bougies de cooldown après sortie

    def get_state(self, symbol: str) -> TradingState:
        """Retourne l'état actuel pour un symbole."""
        return self.states.get(symbol, TradingState.SCANNING)

    def set_state(self, symbol: str, state: TradingState):
        """Change l'état pour un symbole."""
        old_state = self.states.get(symbol, TradingState.SCANNING)
        self.states[symbol] = state
        logger.info(f"{symbol}: État changé de {old_state.value} à {state.value}")

    def arm_signal(self, symbol: str, signal: TradingSignal):
        """
        Arme un signal en attente de confirmation.

        Selon logique.md, un signal doit être confirmé avant exécution.
        """
        self.armed_signals[symbol] = signal
        self.set_state(symbol, TradingState.ARMED)
        logger.info(f"{symbol}: Signal {signal.type} armé, en attente de confirmation")

    def confirm_and_enter(self, symbol: str, entry_price: float) -> Optional[Dict]:
        """
        Confirme un signal armé et entre en position.

        Returns:
            Dict avec les détails de la position si entrée réussie
        """
        if self.get_state(symbol) != TradingState.ARMED:
            return None

        signal = self.armed_signals.get(symbol)
        if not signal:
            return None

        # Entrer en position
        self.position_info[symbol] = {
            'type': signal.type,
            'entry_price': entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'entry_time': datetime.now(),
            'signal': signal
        }

        self.set_state(symbol, TradingState.IN_POSITION)
        del self.armed_signals[symbol]

        logger.info(f"{symbol}: Position {signal.type} ouverte à {entry_price}")
        return self.position_info[symbol]

    def exit_position(self, symbol: str, exit_price: float, reason: str = 'manual') -> Optional[Dict]:
        """
        Sort d'une position et passe en cooldown.

        Args:
            symbol: Symbole
            exit_price: Prix de sortie
            reason: Raison de sortie ('tp', 'sl', 'trailing', 'manual')

        Returns:
            Dict avec les résultats du trade
        """
        if self.get_state(symbol) != TradingState.IN_POSITION:
            return None

        position = self.position_info.get(symbol)
        if not position:
            return None

        # Calculer le P&L
        entry_price = position['entry_price']
        if position['type'] == 'LONG':
            pnl_percent = (exit_price - entry_price) / entry_price * 100
        else:
            pnl_percent = (entry_price - exit_price) / entry_price * 100

        result = {
            'symbol': symbol,
            'type': position['type'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_percent': pnl_percent,
            'exit_reason': reason,
            'duration': (datetime.now() - position['entry_time']).total_seconds()
        }

        # Passer en cooldown
        self.cooldown_bars[symbol] = self.cooldown_duration
        self.set_state(symbol, TradingState.COOLDOWN)

        # Nettoyer
        if symbol in self.position_info:
            del self.position_info[symbol]

        logger.info(f"{symbol}: Position fermée à {exit_price}, P&L: {pnl_percent:.2f}%, raison: {reason}")
        return result

    def update_cooldown(self, symbol: str):
        """
        Met à jour le compteur de cooldown (appelé à chaque nouvelle bougie).
        """
        if self.get_state(symbol) == TradingState.COOLDOWN:
            remaining = self.cooldown_bars.get(symbol, 0)
            if remaining > 1:
                self.cooldown_bars[symbol] = remaining - 1
            else:
                self.cooldown_bars[symbol] = 0
                self.set_state(symbol, TradingState.SCANNING)
                logger.info(f"{symbol}: Cooldown terminé, retour en SCANNING")

    def cancel_armed_signal(self, symbol: str):
        """Annule un signal armé."""
        if symbol in self.armed_signals:
            del self.armed_signals[symbol]
        self.set_state(symbol, TradingState.SCANNING)
        logger.info(f"{symbol}: Signal armé annulé")

    def check_position_exits(self, symbol: str, current_price: float) -> Optional[str]:
        """
        Vérifie si une position doit être fermée (SL/TP).

        Args:
            symbol: Symbole
            current_price: Prix actuel

        Returns:
            Raison de sortie si applicable, sinon None
        """
        if self.get_state(symbol) != TradingState.IN_POSITION:
            return None

        position = self.position_info.get(symbol)
        if not position:
            return None

        if position['type'] == 'LONG':
            if current_price <= position['stop_loss']:
                return 'sl'
            if current_price >= position['take_profit']:
                return 'tp'
        else:  # SHORT
            if current_price >= position['stop_loss']:
                return 'sl'
            if current_price <= position['take_profit']:
                return 'tp'

        return None

    def update_trailing_stop(self, symbol: str, current_price: float, atr: float):
        """
        Met à jour le trailing stop selon logique.md.

        Trailing activé après 1R de profit:
        - Long: stop = max(current_stop, current_price - ATR * multiplier)
        - Short: stop = min(current_stop, current_price + ATR * multiplier)
        """
        if self.get_state(symbol) != TradingState.IN_POSITION:
            return

        position = self.position_info.get(symbol)
        if not position:
            return

        entry = position['entry_price']
        current_sl = position['stop_loss']
        risk = abs(entry - position['stop_loss'])

        # Activer trailing après 1R
        if position['type'] == 'LONG':
            if current_price >= entry + risk:  # 1R profit
                trailing_sl = current_price - (atr * 1.5)
                if trailing_sl > current_sl:
                    position['stop_loss'] = trailing_sl
                    logger.debug(f"{symbol}: Trailing SL mis à jour: {trailing_sl:.2f}")
        else:
            if current_price <= entry - risk:
                trailing_sl = current_price + (atr * 1.5)
                if trailing_sl < current_sl:
                    position['stop_loss'] = trailing_sl
                    logger.debug(f"{symbol}: Trailing SL mis à jour: {trailing_sl:.2f}")

    def get_state_summary(self) -> Dict:
        """Retourne un résumé de l'état de tous les symboles."""
        return {
            'states': {s: st.value for s, st in self.states.items()},
            'armed_signals': len(self.armed_signals),
            'positions': len(self.position_info),
            'in_cooldown': sum(1 for s, st in self.states.items() if st == TradingState.COOLDOWN)
        }

    def generate_all_signals(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
        """
        Génère tous les signaux pour un symbole.

        Args:
            df: DataFrame OHLCV
            symbol: Symbole de trading

        Returns:
            Liste des signaux détectés
        """
        if df is None or df.empty or len(df) < 50:
            return []

        try:
            # Calculer tous les indicateurs
            df = self.technical.calculate_all(df)
            df = self.smc.analyze(df)

            # Vérifier que le DataFrame est toujours valide après calculs
            if df is None or df.empty or len(df) == 0:
                logger.debug(f"DataFrame vide après calcul des indicateurs pour {symbol}")
                return []

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

        except Exception as e:
            logger.warning(f"Erreur lors de la génération des signaux pour {symbol}: {e}")
            return []

    def _calculate_signal_strength(
        self,
        df: pd.DataFrame,
        direction: str,  # 'LONG' or 'SHORT'
        patterns: List[CandlePattern],
        divergences: List[Divergence]
    ) -> tuple:
        """
        Calcule le score de force du signal selon logique.md (0-100).

        Scoring:
        - trend_aligned: +25 points
        - rsi_confirms: +15 points
        - macd_confirms: +10 points
        - volume_above_avg: +20 points
        - htf_aligned: +20 points (via Ichimoku/PSAR)
        - adx bonus: +10 points max
        """
        try:
            last = df.iloc[-1]
        except (IndexError, KeyError):
            return 0, [], {}

        score = 0
        reasons = []
        confirmations = {}

        is_long = direction == 'LONG'

        # 1. TREND ALIGNED (+25 points)
        # close > ema_200 pour long, close < ema_200 pour short
        trend_aligned = False
        if pd.notna(last.get('sma_200')):
            if is_long and last['close'] > last['sma_200']:
                trend_aligned = True
                score += 25
                reasons.append("Tendance alignée (prix > SMA 200)")
            elif not is_long and last['close'] < last['sma_200']:
                trend_aligned = True
                score += 25
                reasons.append("Tendance alignée (prix < SMA 200)")
        confirmations['trend_aligned'] = trend_aligned

        # 2. RSI CONFIRMS (+15 points)
        # Zone neutre (30-70) pour les deux directions
        # Long: RSI < 70 (pas suracheté), idéalement < 50
        # Short: RSI > 30 (pas survendu), idéalement > 50
        rsi = last.get('rsi', 50)
        rsi_confirms = False
        if pd.notna(rsi):
            if is_long:
                if 30 <= rsi <= 70:
                    rsi_confirms = True
                    score += 15
                    reasons.append(f"RSI en zone neutre ({rsi:.1f})")
                elif rsi < 30:
                    rsi_confirms = True
                    score += 15
                    reasons.append(f"RSI survendu ({rsi:.1f}) - opportunité")
            else:
                if 30 <= rsi <= 70:
                    rsi_confirms = True
                    score += 15
                    reasons.append(f"RSI en zone neutre ({rsi:.1f})")
                elif rsi > 70:
                    rsi_confirms = True
                    score += 15
                    reasons.append(f"RSI suracheté ({rsi:.1f}) - opportunité")
        confirmations['rsi_confirms'] = rsi_confirms

        # 3. MACD CONFIRMS (+10 points)
        macd = last.get('macd', 0)
        macd_signal = last.get('macd_signal', 0)
        macd_confirms = False
        if pd.notna(macd) and pd.notna(macd_signal):
            if is_long and macd > macd_signal:
                macd_confirms = True
                score += 10
                reasons.append("MACD haussier")
            elif not is_long and macd < macd_signal:
                macd_confirms = True
                score += 10
                reasons.append("MACD baissier")
        confirmations['macd_confirms'] = macd_confirms

        # 4. VOLUME ABOVE AVG (+20 points)
        volume_ratio = last.get('volume_ratio', 1.0)
        volume_confirms = False
        if pd.notna(volume_ratio) and volume_ratio >= 1.2:
            volume_confirms = True
            score += 20
            reasons.append(f"Volume confirmé ({volume_ratio:.1f}x moyenne)")
        confirmations['volume_above_avg'] = volume_confirms

        # 5. HTF ALIGNED (+20 points) - via Ichimoku et Parabolic SAR
        htf_aligned = False

        # Ichimoku confirmation
        if is_long and last.get('ichimoku_bullish', False):
            htf_aligned = True
            reasons.append("Ichimoku haussier")
        elif not is_long and not last.get('ichimoku_above_cloud', True):
            htf_aligned = True
            reasons.append("Ichimoku baissier")

        # Parabolic SAR confirmation
        psar_bullish = last.get('psar_bullish', None)
        if psar_bullish is not None:
            if is_long and psar_bullish:
                htf_aligned = True
                reasons.append("PSAR haussier")
            elif not is_long and not psar_bullish:
                htf_aligned = True
                reasons.append("PSAR baissier")

        # VWAP confirmation
        if is_long and last.get('above_vwap', False):
            htf_aligned = True
        elif not is_long and last.get('below_vwap', False):
            htf_aligned = True

        if htf_aligned:
            score += 20
        confirmations['htf_aligned'] = htf_aligned

        # 6. ADX BONUS (+10 points max)
        adx = last.get('adx', 0)
        if pd.notna(adx) and adx > 20:
            adx_bonus = min(10, (adx - 20) / 3)
            score += adx_bonus
            if adx > 25:
                reasons.append(f"Tendance établie (ADX {adx:.1f})")
        confirmations['adx'] = adx

        # BONUS: Patterns (+5 points)
        relevant_patterns = [p for p in patterns if
                           (is_long and p.type == 'bullish') or
                           (not is_long and p.type == 'bearish')]
        if relevant_patterns:
            best = max(relevant_patterns, key=lambda p: p.confidence)
            score += 5
            reasons.append(f"Pattern: {best.name}")
            confirmations['pattern'] = best.name

        # BONUS: Divergences (+5 points)
        relevant_divs = [d for d in divergences if
                        (is_long and 'bullish' in d.type) or
                        (not is_long and 'bearish' in d.type)]
        if relevant_divs:
            score += 5
            reasons.append("Divergence confirmée")
            confirmations['divergence'] = True

        # BONUS: SMC (+5 points)
        smc_summary = self.smc.get_structure_summary()
        if is_long:
            if smc_summary.get('active_bullish_ob', 0) > 0:
                score += 2.5
                reasons.append("Order Block haussier")
            if smc_summary.get('active_bullish_fvg', 0) > 0:
                score += 2.5
                reasons.append("FVG haussier")
        else:
            if smc_summary.get('active_bearish_ob', 0) > 0:
                score += 2.5
                reasons.append("Order Block baissier")
            if smc_summary.get('active_bearish_fvg', 0) > 0:
                score += 2.5
                reasons.append("FVG baissier")

        # BONUS: Stochastic confirmation (+5 points)
        stoch_k = last.get('stoch_k', 50)
        if pd.notna(stoch_k):
            if is_long and stoch_k < 80:
                score += 5
            elif not is_long and stoch_k > 20:
                score += 5

        # Cap at 100
        score = min(100, score)

        return score, reasons, confirmations

    def _check_long_signal(
        self,
        df: pd.DataFrame,
        symbol: str,
        patterns: List[CandlePattern],
        divergences: List[Divergence]
    ) -> Optional[TradingSignal]:
        """
        Vérifie les conditions pour un signal long.

        Triple Confirmation selon logique.md:
        1. close > ema_200 (filtre tendance)
        2. rsi > 30 AND rsi < 70 (RSI zone neutre)
        3. macd_line > signal_line (MACD haussier)
        4. adx > 25 (tendance établie)
        5. volume > avg_volume × 1.2 (confirmation volume)
        """
        try:
            if df is None or df.empty or len(df) == 0:
                return None
            last = df.iloc[-1]
        except (IndexError, KeyError) as e:
            logger.debug(f"Cannot access last row for long signal: {e}")
            return None

        # Calcul du score de force (0-100)
        score, reasons, confirmations = self._calculate_signal_strength(
            df, 'LONG', patterns, divergences
        )

        # Vérifier le score minimum
        if score < self.min_strength_score:
            return None

        # Calcul des niveaux de prix
        entry_price = last['close']
        atr = last.get('atr', entry_price * 0.02)

        if pd.isna(atr) or atr == 0:
            atr = entry_price * 0.02

        # Stop et TP basés sur ATR selon logique.md
        # Crypto: multiplicateur 2.5-4.0
        atr_mult = 2.5 if last.get('high_volatility', False) else 2.0
        stop_loss = entry_price - (atr * atr_mult)
        take_profit = entry_price + (atr * atr_mult * self.min_rr_ratio)
        risk_reward = self.min_rr_ratio

        return TradingSignal(
            symbol=symbol,
            type='LONG',
            strength=score / 100.0,
            strength_score=int(score),
            entry_price=round(entry_price, 8),
            stop_loss=round(stop_loss, 8),
            take_profit=round(take_profit, 8),
            risk_reward=risk_reward,
            reasons=reasons,
            indicators=self.technical.get_current_values(df),
            timestamp=datetime.now(),
            strategy='combined',
            confirmations=confirmations
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

        Triple Confirmation selon logique.md (inversé pour short):
        1. close < ema_200 (filtre tendance)
        2. rsi > 30 AND rsi < 70 (RSI zone neutre)
        3. macd_line < signal_line (MACD baissier)
        4. adx > 25 (tendance établie)
        5. volume > avg_volume × 1.2 (confirmation volume)
        """
        try:
            if df is None or df.empty or len(df) == 0:
                return None
            last = df.iloc[-1]
        except (IndexError, KeyError) as e:
            logger.debug(f"Cannot access last row for short signal: {e}")
            return None

        # Calcul du score de force (0-100)
        score, reasons, confirmations = self._calculate_signal_strength(
            df, 'SHORT', patterns, divergences
        )

        # Vérifier le score minimum
        if score < self.min_strength_score:
            return None

        # Calcul des niveaux de prix
        entry_price = last['close']
        atr = last.get('atr', entry_price * 0.02)

        if pd.isna(atr) or atr == 0:
            atr = entry_price * 0.02

        # Stop et TP basés sur ATR selon logique.md
        atr_mult = 2.5 if last.get('high_volatility', False) else 2.0
        stop_loss = entry_price + (atr * atr_mult)
        take_profit = entry_price - (atr * atr_mult * self.min_rr_ratio)
        risk_reward = self.min_rr_ratio

        return TradingSignal(
            symbol=symbol,
            type='SHORT',
            strength=score / 100.0,
            strength_score=int(score),
            entry_price=round(entry_price, 8),
            stop_loss=round(stop_loss, 8),
            take_profit=round(take_profit, 8),
            risk_reward=risk_reward,
            reasons=reasons,
            indicators=self.technical.get_current_values(df),
            timestamp=datetime.now(),
            strategy='combined',
            confirmations=confirmations
        )

    def _signal_to_dict(self, signal: TradingSignal) -> Dict:
        """Convertit un signal en dictionnaire."""
        return {
            'symbol': signal.symbol,
            'type': signal.type,
            'strength': round(signal.strength, 2),
            'strength_score': signal.strength_score,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'risk_reward': signal.risk_reward,
            'reasons': signal.reasons,
            'confirmations': signal.confirmations,
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
        if df is None or df.empty:
            return {'error': 'No data available'}

        try:
            df = self.technical.calculate_all(df)
            df = self.smc.analyze(df)

            # Vérifier que le DataFrame est toujours valide
            if df is None or df.empty or len(df) == 0:
                return {'error': 'DataFrame empty after indicator calculation'}

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

            # Determine trend based on price action
            trend = 'ranging'
            if indicators.get('trend_bias', 0) > 0 and indicators.get('adx', 0) > 25:
                trend = 'uptrend'
            elif indicators.get('trend_bias', 0) < 0 and indicators.get('adx', 0) > 25:
                trend = 'downtrend'

            # Build structure info
            structure = {
                'bias': bias.lower(),
                'trend': trend,
                'support_levels': [],
                'resistance_levels': []
            }

            return {
                'symbol': symbol,
                'bias': bias,
                'bullish_signals': bullish_count,
                'bearish_signals': bearish_count,
                'indicators': indicators,
                'patterns': patterns,
                'divergences': divergences,
                'smc': smc,
                'structure': structure,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse de marché pour {symbol}: {e}")
            return {'error': str(e)}

    def analyze_multi_timeframe(
        self,
        data: Dict[str, pd.DataFrame],
        symbol: str
    ) -> Dict:
        """
        Analyse multi-timeframe selon logique.md.

        Règles MTF:
        - Primary TF (15m): Signaux d'exécution
        - Confirmation TF (1h): Confirmation de direction
        - Trend TF (4h): Biais de tendance HTF

        Scoring MTF:
        - HTF aligned: +20 points
        - Confirmation aligned: +10 points
        - Primary signal: Base score

        Args:
            data: Dict avec les DataFrames par timeframe
            symbol: Symbole

        Returns:
            Dict avec l'analyse MTF
        """
        result = {
            'symbol': symbol,
            'timeframes': {},
            'alignment': 'NEUTRAL',
            'htf_trend': 'NEUTRAL',
            'confirmation_trend': 'NEUTRAL',
            'primary_signal': None,
            'mtf_score_bonus': 0,
            'trade_allowed': False
        }

        # Analyser chaque timeframe
        timeframe_order = ['4h', '1h', '15m']  # Du plus grand au plus petit

        for tf in timeframe_order:
            if tf not in data or data[tf] is None or data[tf].empty:
                continue

            df = data[tf].copy()

            try:
                # Calculer les indicateurs
                df = self.technical.calculate_all(df)

                if df is None or df.empty:
                    continue

                last = df.iloc[-1]

                # Déterminer la tendance de ce TF
                trend = 'NEUTRAL'
                trend_score = 0

                # Prix vs SMA 200
                if pd.notna(last.get('sma_200')):
                    if last['close'] > last['sma_200']:
                        trend_score += 1
                    else:
                        trend_score -= 1

                # Prix vs EMA 50
                if pd.notna(last.get('ema_50')):
                    if last['close'] > last['ema_50']:
                        trend_score += 1
                    else:
                        trend_score -= 1

                # EMA 9 vs EMA 21
                if pd.notna(last.get('ema_9')) and pd.notna(last.get('ema_21')):
                    if last['ema_9'] > last['ema_21']:
                        trend_score += 1
                    else:
                        trend_score -= 1

                # ADX trending
                adx = last.get('adx', 0)
                if pd.notna(adx) and adx > 25:
                    # Confirmer la direction avec +DI/-DI
                    di_pos = last.get('adx_pos', 0)
                    di_neg = last.get('adx_neg', 0)
                    if pd.notna(di_pos) and pd.notna(di_neg):
                        if di_pos > di_neg:
                            trend_score += 1
                        else:
                            trend_score -= 1

                # Ichimoku si disponible
                if last.get('ichimoku_bullish', False):
                    trend_score += 2
                elif last.get('ichimoku_above_cloud', True) is False:
                    trend_score -= 2

                # Déterminer la tendance finale
                if trend_score >= 2:
                    trend = 'BULLISH'
                elif trend_score <= -2:
                    trend = 'BEARISH'
                else:
                    trend = 'NEUTRAL'

                result['timeframes'][tf] = {
                    'trend': trend,
                    'trend_score': trend_score,
                    'close': float(last['close']),
                    'rsi': float(last.get('rsi', 50)) if pd.notna(last.get('rsi')) else 50,
                    'adx': float(adx) if pd.notna(adx) else 0,
                    'above_ema200': last['close'] > last['sma_200'] if pd.notna(last.get('sma_200')) else None
                }

                # Assigner aux catégories
                if tf == '4h':
                    result['htf_trend'] = trend
                elif tf == '1h':
                    result['confirmation_trend'] = trend

            except Exception as e:
                logger.debug(f"Erreur MTF {tf} pour {symbol}: {e}")
                continue

        # Calculer l'alignement MTF
        htf = result['htf_trend']
        conf = result['confirmation_trend']

        # Score bonus MTF
        mtf_bonus = 0

        if htf == 'BULLISH':
            mtf_bonus += 10
            if conf == 'BULLISH':
                mtf_bonus += 10
                result['alignment'] = 'BULLISH'
        elif htf == 'BEARISH':
            mtf_bonus += 10
            if conf == 'BEARISH':
                mtf_bonus += 10
                result['alignment'] = 'BEARISH'
        else:
            # HTF neutre, utiliser confirmation
            if conf != 'NEUTRAL':
                result['alignment'] = conf
                mtf_bonus += 5

        result['mtf_score_bonus'] = mtf_bonus

        # Déterminer si le trade est autorisé
        # On ne trade que si HTF et Confirmation sont alignés
        result['trade_allowed'] = (
            result['alignment'] != 'NEUTRAL' and
            (htf == conf or htf == 'NEUTRAL' or conf == 'NEUTRAL')
        )

        return result

    def generate_signals_with_mtf(
        self,
        data: Dict[str, pd.DataFrame],
        symbol: str
    ) -> List[Dict]:
        """
        Génère des signaux avec confirmation multi-timeframe.

        Args:
            data: Dict avec DataFrames par timeframe (15m, 1h, 4h)
            symbol: Symbole

        Returns:
            Liste des signaux avec score MTF
        """
        # Analyse MTF
        mtf_analysis = self.analyze_multi_timeframe(data, symbol)

        # Récupérer le DataFrame primaire
        primary_tf = '15m'
        if primary_tf not in data or data[primary_tf] is None:
            return []

        df = data[primary_tf]

        # Générer les signaux sur le TF primaire
        signals = self.generate_all_signals(df, symbol)

        # Filtrer et ajuster les signaux selon MTF
        filtered_signals = []

        for signal in signals:
            signal_type = signal.get('type', '')

            # Vérifier l'alignement
            if mtf_analysis['alignment'] == 'BULLISH' and signal_type == 'LONG':
                # Ajouter le bonus MTF
                signal['strength_score'] = min(100, signal.get('strength_score', 0) + mtf_analysis['mtf_score_bonus'])
                signal['strength'] = signal['strength_score'] / 100.0
                signal['confirmations']['mtf_aligned'] = True
                signal['confirmations']['mtf_trend'] = 'BULLISH'
                signal['reasons'].append(f"MTF aligné haussier (+{mtf_analysis['mtf_score_bonus']})")
                filtered_signals.append(signal)

            elif mtf_analysis['alignment'] == 'BEARISH' and signal_type == 'SHORT':
                signal['strength_score'] = min(100, signal.get('strength_score', 0) + mtf_analysis['mtf_score_bonus'])
                signal['strength'] = signal['strength_score'] / 100.0
                signal['confirmations']['mtf_aligned'] = True
                signal['confirmations']['mtf_trend'] = 'BEARISH'
                signal['reasons'].append(f"MTF aligné baissier (+{mtf_analysis['mtf_score_bonus']})")
                filtered_signals.append(signal)

            elif mtf_analysis['alignment'] == 'NEUTRAL':
                # Signaux neutres autorisés mais sans bonus
                signal['confirmations']['mtf_aligned'] = False
                signal['confirmations']['mtf_trend'] = 'NEUTRAL'
                signal['reasons'].append("MTF neutre (prudence)")
                filtered_signals.append(signal)

            # Sinon: signal contre-tendance, ignoré

        return filtered_signals

    def get_mtf_summary(self, data: Dict[str, pd.DataFrame], symbol: str) -> Dict:
        """
        Retourne un résumé MTF pour l'affichage frontend.

        Args:
            data: DataFrames par timeframe
            symbol: Symbole

        Returns:
            Dict résumé pour affichage
        """
        mtf = self.analyze_multi_timeframe(data, symbol)

        return {
            'symbol': symbol,
            'alignment': mtf['alignment'],
            'htf_trend': mtf['htf_trend'],
            'confirmation_trend': mtf['confirmation_trend'],
            'timeframes': mtf['timeframes'],
            'mtf_bonus': mtf['mtf_score_bonus'],
            'trade_allowed': mtf['trade_allowed'],
            'recommendation': self._get_mtf_recommendation(mtf)
        }

    def _get_mtf_recommendation(self, mtf: Dict) -> str:
        """Génère une recommandation textuelle basée sur l'analyse MTF."""
        if mtf['alignment'] == 'BULLISH' and mtf['trade_allowed']:
            return "Biais haussier confirmé - chercher des entrées LONG"
        elif mtf['alignment'] == 'BEARISH' and mtf['trade_allowed']:
            return "Biais baissier confirmé - chercher des entrées SHORT"
        elif not mtf['trade_allowed']:
            return "Timeframes non alignés - attendre une meilleure configuration"
        else:
            return "Tendance neutre - prudence recommandée"
