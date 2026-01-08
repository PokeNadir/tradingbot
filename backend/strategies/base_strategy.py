"""
Classe de base pour toutes les stratégies de trading.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradeProposal:
    """Proposition de trade générée par une stratégie."""
    symbol: str
    direction: str  # 'long' ou 'short'
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float
    risk_reward: float
    confidence: float
    strategy_name: str
    reasons: List[str]
    timestamp: datetime


class BaseStrategy(ABC):
    """
    Classe de base abstraite pour les stratégies de trading.

    Toutes les stratégies doivent implémenter:
    - analyze(): Analyse les données et retourne des signaux
    - should_enter(): Détermine si une entrée est valide
    - calculate_position(): Calcule la taille de position
    """

    def __init__(self, config: dict):
        """
        Initialise la stratégie.

        Args:
            config: Configuration de la stratégie
        """
        self.config = config
        self.name = self.__class__.__name__
        self.enabled = config.get('enabled', True)

    @abstractmethod
    def analyze(self, df: pd.DataFrame, symbol: str) -> Optional[TradeProposal]:
        """
        Analyse les données de marché et génère une proposition de trade.

        Args:
            df: DataFrame avec indicateurs calculés
            symbol: Symbole à analyser

        Returns:
            TradeProposal si les conditions sont remplies, None sinon
        """
        pass

    @abstractmethod
    def should_enter(self, df: pd.DataFrame) -> tuple:
        """
        Détermine si les conditions d'entrée sont remplies.

        Args:
            df: DataFrame avec indicateurs

        Returns:
            Tuple (should_enter: bool, direction: str, reasons: list)
        """
        pass

    def calculate_stop_loss(
        self,
        entry_price: float,
        direction: str,
        atr: float,
        multiplier: float = 2.0
    ) -> float:
        """
        Calcule le niveau de stop-loss basé sur l'ATR.

        Args:
            entry_price: Prix d'entrée
            direction: 'long' ou 'short'
            atr: Valeur ATR actuelle
            multiplier: Multiplicateur ATR

        Returns:
            Niveau de stop-loss
        """
        if direction == 'long':
            return entry_price - (atr * multiplier)
        else:
            return entry_price + (atr * multiplier)

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str,
        risk_reward: float = 2.0
    ) -> float:
        """
        Calcule le niveau de take-profit basé sur le ratio risk/reward.

        Args:
            entry_price: Prix d'entrée
            stop_loss: Niveau de stop-loss
            direction: 'long' ou 'short'
            risk_reward: Ratio risk/reward cible

        Returns:
            Niveau de take-profit
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward

        if direction == 'long':
            return entry_price + reward
        else:
            return entry_price - reward

    def validate_trade(self, proposal: TradeProposal) -> bool:
        """
        Valide une proposition de trade.

        Args:
            proposal: Proposition à valider

        Returns:
            True si le trade est valide
        """
        # Vérifier risk/reward minimum
        min_rr = self.config.get('min_risk_reward', 2.0)
        if proposal.risk_reward < min_rr:
            logger.warning(f"Risk/Reward {proposal.risk_reward} < minimum {min_rr}")
            return False

        # Vérifier confidence minimum
        min_confidence = self.config.get('min_confidence', 0.6)
        if proposal.confidence < min_confidence:
            logger.warning(f"Confidence {proposal.confidence} < minimum {min_confidence}")
            return False

        # Vérifier que stop et take profit sont cohérents
        if proposal.direction == 'long':
            if proposal.stop_loss >= proposal.entry_price:
                return False
            if proposal.take_profit <= proposal.entry_price:
                return False
        else:
            if proposal.stop_loss <= proposal.entry_price:
                return False
            if proposal.take_profit >= proposal.entry_price:
                return False

        return True

    def to_dict(self, proposal: TradeProposal) -> Dict:
        """Convertit une proposition en dictionnaire."""
        return {
            'symbol': proposal.symbol,
            'direction': proposal.direction,
            'entry_price': proposal.entry_price,
            'stop_loss': proposal.stop_loss,
            'take_profit': proposal.take_profit,
            'size': proposal.size,
            'risk_reward': proposal.risk_reward,
            'confidence': proposal.confidence,
            'strategy': proposal.strategy_name,
            'reasons': proposal.reasons,
            'timestamp': proposal.timestamp.isoformat()
        }
