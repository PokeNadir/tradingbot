"""
Module de vérifications pré-trade.

Implémente toutes les vérifications de sécurité avant d'ouvrir une position
(selon TRADING_STRATEGIES_GUIDE.md).
"""

import logging
from typing import Dict, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PreTradeCheckResult:
    """Résultat d'une vérification pré-trade."""
    passed: bool
    check_name: str
    message: str
    severity: str  # 'info', 'warning', 'critical'


class PreTradeChecker:
    """
    Effectue toutes les vérifications avant d'autoriser un trade.

    Vérifications (selon Guide):
    - daily_loss < MAX_DAILY_DRAWDOWN
    - consecutive_losses < 3
    - total_exposure < 6%
    - spread < 0.2%
    - sufficient_liquidity
    - not_in_pause_period
    """

    def __init__(self, config: dict):
        """
        Initialise le checker.

        Args:
            config: Configuration du bot
        """
        self.config = config
        self.risk_config = config.get('risk_management', {})
        self.safety_config = config.get('manipulation', {}).get('safety', {})

    def run_all_checks(
        self,
        capital: float,
        daily_pnl: float,
        consecutive_losses: int,
        open_positions: int,
        total_exposure: float,
        spread: float,
        volume: float,
        avg_volume: float,
        is_paused: bool
    ) -> Tuple[bool, List[PreTradeCheckResult]]:
        """
        Exécute toutes les vérifications pré-trade.

        Args:
            capital: Capital actuel
            daily_pnl: P&L journalier
            consecutive_losses: Nombre de pertes consécutives
            open_positions: Nombre de positions ouvertes
            total_exposure: Exposition totale en %
            spread: Spread actuel
            volume: Volume actuel
            avg_volume: Volume moyen
            is_paused: Si le trading est en pause

        Returns:
            Tuple (tous_checks_passés, liste_résultats)
        """
        results = []

        # Check 1: Pause status
        results.append(self._check_pause_status(is_paused))

        # Check 2: Daily loss
        results.append(self._check_daily_loss(daily_pnl, capital))

        # Check 3: Consecutive losses
        results.append(self._check_consecutive_losses(consecutive_losses))

        # Check 4: Open positions
        results.append(self._check_open_positions(open_positions))

        # Check 5: Total exposure
        results.append(self._check_exposure(total_exposure))

        # Check 6: Spread
        results.append(self._check_spread(spread))

        # Check 7: Liquidity
        results.append(self._check_liquidity(volume, avg_volume))

        # Déterminer si tous les checks critiques sont passés
        all_passed = all(r.passed for r in results if r.severity == 'critical')

        return all_passed, results

    def _check_pause_status(self, is_paused: bool) -> PreTradeCheckResult:
        """Vérifie si le trading n'est pas en pause."""
        if is_paused:
            return PreTradeCheckResult(
                passed=False,
                check_name="pause_status",
                message="Trading en pause suite à pertes consécutives",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="pause_status",
            message="Trading actif",
            severity="info"
        )

    def _check_daily_loss(self, daily_pnl: float, capital: float) -> PreTradeCheckResult:
        """Vérifie la perte journalière."""
        max_daily_loss = self.risk_config.get('drawdown', {}).get('daily_loss_limit', 0.03)
        daily_loss_percent = abs(daily_pnl) / capital if capital > 0 else 0

        if daily_pnl < 0 and daily_loss_percent >= max_daily_loss:
            return PreTradeCheckResult(
                passed=False,
                check_name="daily_loss",
                message=f"Perte journalière ({daily_loss_percent*100:.1f}%) >= limite ({max_daily_loss*100}%)",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="daily_loss",
            message=f"P&L journalier: {daily_loss_percent*100:.1f}% (limite: {max_daily_loss*100}%)",
            severity="info"
        )

    def _check_consecutive_losses(self, consecutive_losses: int) -> PreTradeCheckResult:
        """Vérifie le nombre de pertes consécutives."""
        max_consecutive = self.risk_config.get('drawdown', {}).get('consecutive_loss_pause', 3)

        if consecutive_losses >= max_consecutive:
            return PreTradeCheckResult(
                passed=False,
                check_name="consecutive_losses",
                message=f"{consecutive_losses} pertes consécutives >= limite ({max_consecutive})",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="consecutive_losses",
            message=f"{consecutive_losses} pertes consécutives (limite: {max_consecutive})",
            severity="info"
        )

    def _check_open_positions(self, open_positions: int) -> PreTradeCheckResult:
        """Vérifie le nombre de positions ouvertes."""
        max_positions = self.risk_config.get('max_open_positions', 3)

        if open_positions >= max_positions:
            return PreTradeCheckResult(
                passed=False,
                check_name="open_positions",
                message=f"{open_positions} positions >= max ({max_positions})",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="open_positions",
            message=f"{open_positions}/{max_positions} positions",
            severity="info"
        )

    def _check_exposure(self, total_exposure: float) -> PreTradeCheckResult:
        """Vérifie l'exposition totale."""
        max_exposure = self.risk_config.get('max_risk_total', 0.06)

        if total_exposure >= max_exposure:
            return PreTradeCheckResult(
                passed=False,
                check_name="exposure",
                message=f"Exposition ({total_exposure*100:.1f}%) >= max ({max_exposure*100}%)",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="exposure",
            message=f"Exposition: {total_exposure*100:.1f}% (max: {max_exposure*100}%)",
            severity="info"
        )

    def _check_spread(self, spread: float) -> PreTradeCheckResult:
        """Vérifie le spread."""
        max_spread = self.safety_config.get('max_spread_percent', 0.002)

        if spread > max_spread:
            return PreTradeCheckResult(
                passed=False,
                check_name="spread",
                message=f"Spread ({spread*100:.3f}%) > max ({max_spread*100}%)",
                severity="critical"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="spread",
            message=f"Spread: {spread*100:.3f}% (max: {max_spread*100}%)",
            severity="info"
        )

    def _check_liquidity(self, volume: float, avg_volume: float) -> PreTradeCheckResult:
        """Vérifie la liquidité suffisante."""
        if avg_volume == 0:
            return PreTradeCheckResult(
                passed=False,
                check_name="liquidity",
                message="Volume moyen non disponible",
                severity="warning"
            )

        volume_ratio = volume / avg_volume
        min_ratio = 0.5  # Volume actuel doit être au moins 50% du moyen

        if volume_ratio < min_ratio:
            return PreTradeCheckResult(
                passed=False,
                check_name="liquidity",
                message=f"Volume faible ({volume_ratio*100:.0f}% du moyen)",
                severity="warning"
            )
        return PreTradeCheckResult(
            passed=True,
            check_name="liquidity",
            message=f"Volume: {volume_ratio*100:.0f}% du moyen",
            severity="info"
        )
