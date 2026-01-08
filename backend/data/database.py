"""
Module de base de données SQLite pour le stockage des trades et données.
"""

import aiosqlite
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    Gère la persistance des données de trading.

    Tables:
    - trades: Historique des trades
    - signals: Signaux générés
    - portfolio_snapshots: Snapshots du portfolio
    - ohlcv_cache: Cache des données OHLCV
    """

    def __init__(self, config: dict):
        """
        Initialise la base de données.

        Args:
            config: Configuration contenant database.path
        """
        self.config = config
        db_path = config.get('database', {}).get('path', 'data/trades.db')
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init(self):
        """Initialise les tables de la base de données."""
        async with aiosqlite.connect(self.db_path) as db:
            # Trades table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    size REAL NOT NULL,
                    stop_loss REAL,
                    take_profit REAL,
                    status TEXT DEFAULT 'open',
                    pnl REAL,
                    pnl_percent REAL,
                    fees REAL,
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP,
                    strategy TEXT,
                    signals TEXT,
                    notes TEXT
                )
            ''')

            # Signals table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    strength REAL NOT NULL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    reasons TEXT,
                    indicators TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed INTEGER DEFAULT 0
                )
            ''')

            # Portfolio snapshots
            await db.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capital REAL NOT NULL,
                    equity REAL NOT NULL,
                    open_pnl REAL,
                    closed_pnl REAL,
                    positions TEXT,
                    drawdown REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Daily statistics
            await db.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    starting_capital REAL,
                    ending_capital REAL,
                    pnl REAL,
                    pnl_percent REAL,
                    trades_count INTEGER,
                    win_count INTEGER,
                    loss_count INTEGER,
                    win_rate REAL,
                    max_drawdown REAL,
                    best_trade REAL,
                    worst_trade REAL
                )
            ''')

            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")

    async def save_trade(self, trade: dict) -> str:
        """
        Sauvegarde un trade.

        Args:
            trade: Dictionnaire du trade

        Returns:
            ID du trade
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO trades (
                    id, symbol, direction, entry_price, exit_price, size,
                    stop_loss, take_profit, status, pnl, pnl_percent, fees,
                    entry_time, exit_time, strategy, signals, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.get('id'),
                trade.get('symbol'),
                trade.get('direction'),
                trade.get('entry_price'),
                trade.get('exit_price'),
                trade.get('size'),
                trade.get('stop_loss'),
                trade.get('take_profit'),
                trade.get('status', 'open'),
                trade.get('pnl'),
                trade.get('pnl_percent'),
                trade.get('fees'),
                trade.get('entry_time'),
                trade.get('exit_time'),
                trade.get('strategy'),
                json.dumps(trade.get('signals', [])),
                trade.get('notes')
            ))
            await db.commit()
            return trade.get('id')

    async def update_trade(self, trade_id: str, updates: dict):
        """
        Met à jour un trade existant.

        Args:
            trade_id: ID du trade
            updates: Champs à mettre à jour
        """
        set_clauses = []
        values = []

        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)

        values.append(trade_id)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE trades SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            await db.commit()

    async def get_trade(self, trade_id: str) -> Optional[dict]:
        """Récupère un trade par son ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM trades WHERE id = ?", (trade_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_open_trades(self) -> List[dict]:
        """Récupère tous les trades ouverts."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM trades WHERE status = 'open' ORDER BY entry_time DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_trade_history(
        self,
        limit: int = 100,
        symbol: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> List[dict]:
        """
        Récupère l'historique des trades.

        Args:
            limit: Nombre max de trades
            symbol: Filtrer par symbole
            start_date: Date de début
            end_date: Date de fin

        Returns:
            Liste des trades
        """
        query = "SELECT * FROM trades WHERE status = 'closed'"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if start_date:
            query += " AND entry_time >= ?"
            params.append(start_date)
        if end_date:
            query += " AND entry_time <= ?"
            params.append(end_date)

        query += f" ORDER BY exit_time DESC LIMIT {limit}"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def save_signal(self, signal: dict) -> int:
        """
        Sauvegarde un signal.

        Args:
            signal: Dictionnaire du signal

        Returns:
            ID du signal
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO signals (
                    symbol, signal_type, direction, strength, entry_price,
                    stop_loss, take_profit, reasons, indicators
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.get('symbol'),
                signal.get('type'),
                signal.get('direction'),
                signal.get('strength'),
                signal.get('entry_price'),
                signal.get('stop_loss'),
                signal.get('take_profit'),
                json.dumps(signal.get('reasons', [])),
                json.dumps(signal.get('indicators', {}))
            ))
            await db.commit()
            return cursor.lastrowid

    async def save_portfolio_snapshot(self, snapshot: dict):
        """Sauvegarde un snapshot du portfolio."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO portfolio_snapshots (
                    capital, equity, open_pnl, closed_pnl, positions, drawdown
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                snapshot.get('capital'),
                snapshot.get('equity'),
                snapshot.get('open_pnl'),
                snapshot.get('closed_pnl'),
                json.dumps(snapshot.get('positions', [])),
                snapshot.get('drawdown')
            ))
            await db.commit()

    async def get_trading_stats(self, days: int = 30) -> dict:
        """
        Calcule les statistiques de trading.

        Args:
            days: Nombre de jours à considérer

        Returns:
            Dict avec les statistiques
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Total trades
            async with db.execute(
                "SELECT COUNT(*) FROM trades WHERE status = 'closed' "
                "AND exit_time >= datetime('now', ?)",
                (f'-{days} days',)
            ) as cursor:
                total_trades = (await cursor.fetchone())[0]

            # Winning trades
            async with db.execute(
                "SELECT COUNT(*) FROM trades WHERE status = 'closed' AND pnl > 0 "
                "AND exit_time >= datetime('now', ?)",
                (f'-{days} days',)
            ) as cursor:
                winning_trades = (await cursor.fetchone())[0]

            # Total P&L
            async with db.execute(
                "SELECT SUM(pnl) FROM trades WHERE status = 'closed' "
                "AND exit_time >= datetime('now', ?)",
                (f'-{days} days',)
            ) as cursor:
                total_pnl = (await cursor.fetchone())[0] or 0

            # Average win/loss
            async with db.execute(
                "SELECT AVG(pnl) FROM trades WHERE status = 'closed' AND pnl > 0 "
                "AND exit_time >= datetime('now', ?)",
                (f'-{days} days',)
            ) as cursor:
                avg_win = (await cursor.fetchone())[0] or 0

            async with db.execute(
                "SELECT AVG(pnl) FROM trades WHERE status = 'closed' AND pnl < 0 "
                "AND exit_time >= datetime('now', ?)",
                (f'-{days} days',)
            ) as cursor:
                avg_loss = (await cursor.fetchone())[0] or 0

            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': round(win_rate, 4),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(profit_factor, 2),
                'period_days': days
            }
