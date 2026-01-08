"""
Module de gestion du portfolio.

Gère les positions ouvertes, le capital, et les statistiques de performance.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Position ouverte."""
    id: str
    symbol: str
    direction: str  # 'long' ou 'short'
    entry_price: float
    current_price: float
    size: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    pnl: float = 0
    pnl_percent: float = 0
    strategy: str = ''
    trailing_stop: Optional[float] = None


@dataclass
class PortfolioStats:
    """Statistiques du portfolio."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0
    total_pnl: float = 0
    avg_win: float = 0
    avg_loss: float = 0
    profit_factor: float = 0
    max_drawdown: float = 0
    best_trade: float = 0
    worst_trade: float = 0


class Portfolio:
    """
    Gère le portfolio de trading.

    Fonctionnalités:
    - Suivi du capital et de l'équité
    - Gestion des positions ouvertes
    - Calcul des statistiques de performance
    """

    def __init__(self, config: dict):
        """
        Initialise le portfolio.

        Args:
            config: Configuration du bot
        """
        self.config = config
        paper_config = config.get('paper_trading', {})
        self.initial_capital = paper_config.get('initial_capital', 10000)
        self.currency = paper_config.get('currency', 'USDT')

        # État du portfolio
        self.capital = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[Dict] = []

        # Statistiques
        self.stats = PortfolioStats()
        self.peak_equity = self.initial_capital
        self.current_drawdown = 0

    def get_equity(self) -> float:
        """
        Calcule l'équité totale (capital + PnL non réalisé).

        Returns:
            Équité totale
        """
        unrealized_pnl = sum(pos.pnl for pos in self.positions.values())
        return self.capital + unrealized_pnl

    def get_open_pnl(self) -> float:
        """Retourne le P&L non réalisé total."""
        return sum(pos.pnl for pos in self.positions.values())

    def get_exposure(self) -> float:
        """
        Calcule l'exposition totale en pourcentage du capital.

        Returns:
            Exposition en décimal (0.05 = 5%)
        """
        if self.capital <= 0:
            return 0

        total_exposure = sum(
            pos.size * pos.current_price
            for pos in self.positions.values()
        )
        return total_exposure / self.capital

    def open_position(
        self,
        position_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        size: float,
        stop_loss: float,
        take_profit: float,
        strategy: str = ''
    ) -> Position:
        """
        Ouvre une nouvelle position.

        Args:
            position_id: ID unique de la position
            symbol: Symbole tradé
            direction: 'long' ou 'short'
            entry_price: Prix d'entrée
            size: Taille de la position
            stop_loss: Niveau de stop-loss
            take_profit: Niveau de take-profit
            strategy: Nom de la stratégie

        Returns:
            Position créée
        """
        position = Position(
            id=position_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            current_price=entry_price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.now(),
            strategy=strategy
        )

        self.positions[position_id] = position
        logger.info(f"Position ouverte: {direction.upper()} {symbol} @ {entry_price} | Size: {size}")

        return position

    def update_position_price(self, position_id: str, current_price: float):
        """
        Met à jour le prix actuel d'une position et recalcule le P&L.

        Args:
            position_id: ID de la position
            current_price: Prix actuel
        """
        if position_id not in self.positions:
            return

        position = self.positions[position_id]
        position.current_price = current_price

        # Calcul du P&L
        if position.direction == 'long':
            position.pnl = (current_price - position.entry_price) * position.size
        else:
            position.pnl = (position.entry_price - current_price) * position.size

        position.pnl_percent = (position.pnl / (position.entry_price * position.size)) * 100

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        fees: float = 0
    ) -> Dict:
        """
        Ferme une position.

        Args:
            position_id: ID de la position
            exit_price: Prix de sortie
            fees: Frais de trading

        Returns:
            Dict avec les détails du trade fermé
        """
        if position_id not in self.positions:
            return {'error': 'Position not found'}

        position = self.positions[position_id]

        # Calcul du P&L final
        if position.direction == 'long':
            gross_pnl = (exit_price - position.entry_price) * position.size
        else:
            gross_pnl = (position.entry_price - exit_price) * position.size

        net_pnl = gross_pnl - fees

        # Mise à jour du capital
        self.capital += net_pnl

        # Mise à jour du drawdown
        equity = self.get_equity()
        if equity > self.peak_equity:
            self.peak_equity = equity
        self.current_drawdown = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0

        # Enregistrer le trade fermé
        closed_trade = {
            'id': position_id,
            'symbol': position.symbol,
            'direction': position.direction,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'size': position.size,
            'gross_pnl': round(gross_pnl, 2),
            'fees': round(fees, 2),
            'net_pnl': round(net_pnl, 2),
            'pnl_percent': round((net_pnl / (position.entry_price * position.size)) * 100, 2),
            'entry_time': position.entry_time.isoformat(),
            'exit_time': datetime.now().isoformat(),
            'strategy': position.strategy,
            'holding_time': str(datetime.now() - position.entry_time)
        }

        self.closed_trades.append(closed_trade)
        self._update_stats(net_pnl)

        # Supprimer la position
        del self.positions[position_id]

        logger.info(f"Position fermée: {position.symbol} | P&L: {net_pnl:.2f} ({closed_trade['pnl_percent']:.2f}%)")

        return closed_trade

    def _update_stats(self, pnl: float):
        """
        Met à jour les statistiques de trading.

        Args:
            pnl: P&L du trade fermé
        """
        self.stats.total_trades += 1

        if pnl > 0:
            self.stats.winning_trades += 1
            self.stats.avg_win = (
                (self.stats.avg_win * (self.stats.winning_trades - 1) + pnl)
                / self.stats.winning_trades
            )
            if pnl > self.stats.best_trade:
                self.stats.best_trade = pnl
        else:
            self.stats.losing_trades += 1
            self.stats.avg_loss = (
                (self.stats.avg_loss * (self.stats.losing_trades - 1) + abs(pnl))
                / self.stats.losing_trades
            )
            if pnl < self.stats.worst_trade:
                self.stats.worst_trade = pnl

        self.stats.total_pnl += pnl
        self.stats.win_rate = self.stats.winning_trades / self.stats.total_trades if self.stats.total_trades > 0 else 0

        if self.stats.avg_loss > 0:
            self.stats.profit_factor = self.stats.avg_win / self.stats.avg_loss
        else:
            self.stats.profit_factor = 0

        if self.current_drawdown > self.stats.max_drawdown:
            self.stats.max_drawdown = self.current_drawdown

    def check_stops(self, symbol: str, current_price: float) -> List[Dict]:
        """
        Vérifie si des stops ou take-profits sont atteints.

        Args:
            symbol: Symbole à vérifier
            current_price: Prix actuel

        Returns:
            Liste des positions à fermer
        """
        positions_to_close = []

        for pos_id, position in self.positions.items():
            if position.symbol != symbol:
                continue

            # Mettre à jour le prix
            self.update_position_price(pos_id, current_price)

            # Vérifier stop-loss
            if position.direction == 'long':
                if current_price <= position.stop_loss:
                    positions_to_close.append({
                        'id': pos_id,
                        'reason': 'stop_loss',
                        'price': current_price
                    })
                elif current_price >= position.take_profit:
                    positions_to_close.append({
                        'id': pos_id,
                        'reason': 'take_profit',
                        'price': current_price
                    })
            else:  # short
                if current_price >= position.stop_loss:
                    positions_to_close.append({
                        'id': pos_id,
                        'reason': 'stop_loss',
                        'price': current_price
                    })
                elif current_price <= position.take_profit:
                    positions_to_close.append({
                        'id': pos_id,
                        'reason': 'take_profit',
                        'price': current_price
                    })

        return positions_to_close

    def get_summary(self) -> Dict:
        """
        Retourne un résumé du portfolio.

        Returns:
            Dict avec toutes les informations
        """
        equity = self.get_equity()
        return {
            'capital': round(self.capital, 2),
            'equity': round(equity, 2),
            'initial_capital': self.initial_capital,
            'total_return': round(((equity / self.initial_capital) - 1) * 100, 2),
            'open_pnl': round(self.get_open_pnl(), 2),
            'open_positions': len(self.positions),
            'exposure': round(self.get_exposure() * 100, 2),
            'current_drawdown': round(self.current_drawdown * 100, 2),
            'currency': self.currency,
            'stats': {
                'total_trades': self.stats.total_trades,
                'winning_trades': self.stats.winning_trades,
                'losing_trades': self.stats.losing_trades,
                'win_rate': round(self.stats.win_rate * 100, 2),
                'total_pnl': round(self.stats.total_pnl, 2),
                'avg_win': round(self.stats.avg_win, 2),
                'avg_loss': round(self.stats.avg_loss, 2),
                'profit_factor': round(self.stats.profit_factor, 2),
                'max_drawdown': round(self.stats.max_drawdown * 100, 2),
                'best_trade': round(self.stats.best_trade, 2),
                'worst_trade': round(self.stats.worst_trade, 2)
            }
        }

    def get_positions_list(self) -> List[Dict]:
        """
        Retourne la liste des positions ouvertes.

        Returns:
            Liste de dictionnaires
        """
        return [
            {
                'id': pos.id,
                'symbol': pos.symbol,
                'direction': pos.direction,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'size': pos.size,
                'stop_loss': pos.stop_loss,
                'take_profit': pos.take_profit,
                'pnl': round(pos.pnl, 2),
                'pnl_percent': round(pos.pnl_percent, 2),
                'entry_time': pos.entry_time.isoformat(),
                'strategy': pos.strategy
            }
            for pos in self.positions.values()
        ]

    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """
        Retourne les trades récents.

        Args:
            limit: Nombre maximum de trades

        Returns:
            Liste des trades
        """
        return self.closed_trades[-limit:][::-1]
