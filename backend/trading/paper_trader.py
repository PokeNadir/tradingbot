"""
Module de paper trading.

Simule l'exécution des trades sans risque réel.
"""

from typing import Dict, Optional, List
from datetime import datetime
import uuid
import logging

from backend.trading.portfolio import Portfolio
from backend.trading.risk_manager import RiskManager
from backend.trading.pre_trade_checks import PreTradeChecker

logger = logging.getLogger(__name__)


class PaperTrader:
    """
    Moteur de paper trading.

    Simule l'exécution des trades avec:
    - Gestion du portfolio
    - Gestion des risques
    - Vérifications pré-trade
    - Simulation du slippage et des frais
    """

    def __init__(
        self,
        config: dict,
        portfolio: Portfolio,
        risk_manager: RiskManager
    ):
        """
        Initialise le paper trader.

        Args:
            config: Configuration du bot
            portfolio: Instance du portfolio
            risk_manager: Instance du risk manager
        """
        self.config = config
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.pre_trade_checker = PreTradeChecker(config)

        # Configuration des coûts
        costs_config = config.get('costs', {})
        self.commission_percent = costs_config.get('commission_percent', 0.001)
        self.slippage = costs_config.get('slippage', {}).get('liquid_majors', 0.0001)

        # Historique des signaux
        self.signal_history: List[Dict] = []

    async def execute_signal(self, signal: Dict) -> Dict:
        """
        Exécute un signal de trading.

        Args:
            signal: Signal à exécuter

        Returns:
            Dict avec le résultat de l'exécution
        """
        if not signal:
            return {'error': 'No signal provided'}

        symbol = signal.get('symbol')
        direction = signal.get('type', '').lower()
        entry_price = signal.get('entry_price')
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')

        if not all([symbol, direction, entry_price, stop_loss, take_profit]):
            return {'error': 'Signal incomplet'}

        # Enregistrer le signal
        self.signal_history.append({
            **signal,
            'received_at': datetime.now().isoformat(),
            'status': 'pending'
        })

        # Vérifications pré-trade
        capital = self.portfolio.capital
        open_positions = len(self.portfolio.positions)
        exposure = self.portfolio.get_exposure()
        spread = 0.0001  # Simulé

        can_trade, reason = self.risk_manager.check_pre_trade_conditions(
            capital=capital,
            current_positions=open_positions,
            current_exposure=exposure,
            spread_percent=spread
        )

        if not can_trade:
            logger.warning(f"Trade refusé: {reason}")
            return {
                'status': 'rejected',
                'reason': reason,
                'signal': signal
            }

        # Calculer la taille de position
        position_size = self.risk_manager.calculate_position_size(
            capital=capital,
            entry_price=entry_price,
            stop_loss=stop_loss
        )

        # Appliquer le slippage
        if direction == 'long':
            executed_price = entry_price * (1 + self.slippage)
        else:
            executed_price = entry_price * (1 - self.slippage)

        # Calculer les frais
        position_value = position_size.size * executed_price
        fees = position_value * self.commission_percent

        # Vérifier que nous avons assez de capital
        required_capital = position_value + fees
        if required_capital > capital:
            return {
                'status': 'rejected',
                'reason': f'Capital insuffisant: {capital:.2f} < {required_capital:.2f}',
                'signal': signal
            }

        # Ouvrir la position
        position_id = str(uuid.uuid4())[:8]
        position = self.portfolio.open_position(
            position_id=position_id,
            symbol=symbol,
            direction=direction,
            entry_price=executed_price,
            size=position_size.size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy=signal.get('strategy', 'manual')
        )

        logger.info(
            f"Trade exécuté: {direction.upper()} {symbol} @ {executed_price:.2f} | "
            f"Size: {position_size.size:.4f} | Risk: {position_size.risk_amount:.2f} ({position_size.risk_percent*100:.1f}%)"
        )

        return {
            'status': 'executed',
            'position_id': position_id,
            'symbol': symbol,
            'direction': direction,
            'entry_price': round(executed_price, 2),
            'size': position_size.size,
            'size_quote': position_size.size_quote,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': position_size.risk_amount,
            'risk_percent': round(position_size.risk_percent * 100, 2),
            'fees': round(fees, 2),
            'timestamp': datetime.now().isoformat()
        }

    async def update_prices(self, prices: Dict[str, float]) -> List[Dict]:
        """
        Met à jour les prix et vérifie les stops.

        Args:
            prices: Dict avec {symbol: price}

        Returns:
            Liste des positions fermées
        """
        closed_positions = []

        for symbol, price in prices.items():
            # Vérifier les stops
            positions_to_close = self.portfolio.check_stops(symbol, price)

            for close_info in positions_to_close:
                # Appliquer le slippage à la sortie
                position = self.portfolio.positions.get(close_info['id'])
                if not position:
                    continue

                exit_price = close_info['price']
                if close_info['reason'] == 'stop_loss':
                    # Slippage défavorable sur les stops
                    if position.direction == 'long':
                        exit_price *= (1 - self.slippage)
                    else:
                        exit_price *= (1 + self.slippage)

                # Calculer les frais de sortie
                exit_value = position.size * exit_price
                fees = exit_value * self.commission_percent

                # Fermer la position
                result = self.portfolio.close_position(
                    close_info['id'],
                    exit_price,
                    fees
                )

                # Mettre à jour le risk manager
                self.risk_manager.update_trade_result(
                    result['net_pnl'],
                    self.portfolio.capital
                )

                closed_positions.append({
                    **result,
                    'close_reason': close_info['reason']
                })

                logger.info(
                    f"Position fermée ({close_info['reason']}): {symbol} | "
                    f"P&L: {result['net_pnl']:.2f}"
                )

        return closed_positions

    async def close_position_manual(
        self,
        position_id: str,
        current_price: float
    ) -> Dict:
        """
        Ferme manuellement une position.

        Args:
            position_id: ID de la position
            current_price: Prix actuel

        Returns:
            Dict avec le résultat
        """
        position = self.portfolio.positions.get(position_id)
        if not position:
            return {'error': 'Position not found'}

        # Appliquer le slippage
        if position.direction == 'long':
            exit_price = current_price * (1 - self.slippage)
        else:
            exit_price = current_price * (1 + self.slippage)

        # Calculer les frais
        exit_value = position.size * exit_price
        fees = exit_value * self.commission_percent

        # Fermer
        result = self.portfolio.close_position(position_id, exit_price, fees)

        # Mettre à jour les stats
        self.risk_manager.update_trade_result(
            result['net_pnl'],
            self.portfolio.capital
        )

        return {
            **result,
            'close_reason': 'manual'
        }

    async def close_all_positions(self, prices: Dict[str, float]) -> List[Dict]:
        """
        Ferme toutes les positions ouvertes.

        Args:
            prices: Dict avec les prix actuels {symbol: price}

        Returns:
            Liste des positions fermées
        """
        results = []

        for position_id in list(self.portfolio.positions.keys()):
            position = self.portfolio.positions.get(position_id)
            if position and position.symbol in prices:
                result = await self.close_position_manual(
                    position_id,
                    prices[position.symbol]
                )
                results.append(result)

        return results

    def get_status(self) -> Dict:
        """
        Retourne le statut complet du paper trader.

        Returns:
            Dict avec toutes les informations
        """
        portfolio_summary = self.portfolio.get_summary()
        risk_summary = self.risk_manager.get_risk_summary(self.portfolio.capital)

        return {
            'mode': 'paper',
            'portfolio': portfolio_summary,
            'risk': risk_summary,
            'open_positions': self.portfolio.get_positions_list(),
            'recent_trades': self.portfolio.get_recent_trades(10),
            'signals_received': len(self.signal_history),
            'commission_percent': self.commission_percent * 100,
            'slippage_percent': self.slippage * 100
        }

    def get_performance_metrics(self) -> Dict:
        """
        Calcule les métriques de performance détaillées.

        Returns:
            Dict avec les métriques
        """
        stats = self.portfolio.stats
        closed_trades = self.portfolio.closed_trades

        if not closed_trades:
            return {
                'message': 'Pas assez de trades pour calculer les métriques',
                'total_trades': 0
            }

        # Calculer les métriques avancées
        pnls = [t['net_pnl'] for t in closed_trades]
        winning_pnls = [p for p in pnls if p > 0]
        losing_pnls = [abs(p) for p in pnls if p < 0]

        # Sharpe Ratio simplifié (sans taux sans risque)
        import numpy as np
        if len(pnls) > 1:
            avg_return = np.mean(pnls)
            std_return = np.std(pnls)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0

        # Calcul du max drawdown séquentiel
        equity_curve = [self.portfolio.initial_capital]
        for pnl in pnls:
            equity_curve.append(equity_curve[-1] + pnl)

        peak = equity_curve[0]
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_pnls),
            'losing_trades': len(losing_pnls),
            'win_rate': round(len(winning_pnls) / len(closed_trades) * 100, 2) if closed_trades else 0,
            'total_pnl': round(sum(pnls), 2),
            'avg_pnl': round(np.mean(pnls), 2) if pnls else 0,
            'avg_win': round(np.mean(winning_pnls), 2) if winning_pnls else 0,
            'avg_loss': round(np.mean(losing_pnls), 2) if losing_pnls else 0,
            'best_trade': round(max(pnls), 2) if pnls else 0,
            'worst_trade': round(min(pnls), 2) if pnls else 0,
            'profit_factor': round(sum(winning_pnls) / sum(losing_pnls), 2) if losing_pnls and sum(losing_pnls) > 0 else 0,
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown_percent': round(max_dd * 100, 2),
            'expectancy': round(
                (stats.win_rate * stats.avg_win) - ((1 - stats.win_rate) * stats.avg_loss), 2
            ) if stats.total_trades > 0 else 0
        }
