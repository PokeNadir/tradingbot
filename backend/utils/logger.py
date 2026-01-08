"""
Module de logging pour le bot de trading.
Utilise Rich pour un affichage formaté dans le terminal.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Custom theme for trading bot
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "trade_long": "bold green",
    "trade_short": "bold red",
    "signal": "bold magenta",
})

console = Console(theme=custom_theme)


def setup_logger(
    name: str = "trading_bot",
    level: int = logging.INFO,
    log_file: bool = True
) -> logging.Logger:
    """
    Configure le logger avec Rich handler et fichier optionnel.

    Args:
        name: Nom du logger
        level: Niveau de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Créer un fichier de log

    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Éviter les handlers dupliqués
    if logger.handlers:
        return logger

    # Rich handler pour le terminal
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True
    )
    rich_handler.setLevel(level)
    rich_format = logging.Formatter("%(message)s")
    rich_handler.setFormatter(rich_format)
    logger.addHandler(rich_handler)

    # File handler optionnel
    if log_file:
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def log_trade(
    logger: logging.Logger,
    direction: str,
    symbol: str,
    entry: float,
    size: float,
    stop_loss: float,
    take_profit: float
):
    """
    Log un trade avec formatage spécial.

    Args:
        logger: Instance du logger
        direction: 'LONG' ou 'SHORT'
        symbol: Symbole tradé
        entry: Prix d'entrée
        size: Taille de position
        stop_loss: Niveau stop-loss
        take_profit: Niveau take-profit
    """
    style = "trade_long" if direction == "LONG" else "trade_short"
    console.print(
        f"[{style}]{direction}[/{style}] {symbol} @ {entry:.2f} | "
        f"Size: {size:.4f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}",
        style=style
    )
    logger.info(
        f"TRADE: {direction} {symbol} @ {entry} | Size: {size} | SL: {stop_loss} | TP: {take_profit}"
    )


def log_signal(
    logger: logging.Logger,
    signal_type: str,
    symbol: str,
    strength: float,
    reason: str
):
    """
    Log un signal de trading.

    Args:
        logger: Instance du logger
        signal_type: Type de signal
        symbol: Symbole concerné
        strength: Force du signal (0-1)
        reason: Raison du signal
    """
    console.print(
        f"[signal]SIGNAL[/signal] {signal_type} on {symbol} | "
        f"Strength: {strength:.0%} | {reason}",
        style="signal"
    )
    logger.info(f"SIGNAL: {signal_type} {symbol} | Strength: {strength} | {reason}")


# Logger par défaut
logger = setup_logger()
