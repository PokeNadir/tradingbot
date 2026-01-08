"""
Configuration loader for the trading bot.
Charge la configuration depuis le fichier YAML et les variables d'environnement.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing all configuration
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Override with environment variables
    if os.getenv('EXCHANGE'):
        config['exchange']['name'] = os.getenv('EXCHANGE')
    if os.getenv('TESTNET'):
        config['exchange']['testnet'] = os.getenv('TESTNET').lower() == 'true'
    if os.getenv('INITIAL_CAPITAL'):
        config['paper_trading']['initial_capital'] = float(os.getenv('INITIAL_CAPITAL'))
    if os.getenv('DATABASE_URL'):
        config['database']['url'] = os.getenv('DATABASE_URL')

    # On-chain API keys
    if os.getenv('GLASSNODE_API_KEY'):
        config['onchain']['glassnode_api_key'] = os.getenv('GLASSNODE_API_KEY')
        config['onchain']['enabled'] = True
    if os.getenv('COINGLASS_API_KEY'):
        config['onchain']['coinglass_api_key'] = os.getenv('COINGLASS_API_KEY')

    return config


# Global config instance
try:
    CONFIG = load_config()
except FileNotFoundError:
    CONFIG = {}
