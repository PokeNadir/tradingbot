"""
Module d'analyse on-chain.

Récupère les métriques on-chain depuis les APIs:
- Glassnode: MVRV, NUPL, SOPR, exchange flows
- CoinGlass: Funding rates, Open Interest, liquidations
"""

import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OnChainAnalyzer:
    """
    Analyse les métriques on-chain pour Bitcoin et Ethereum.

    Seuils selon TRADING_STRATEGIES_GUIDE.md:
    - MVRV > 3.5: Euphorie extrême (VENDRE)
    - MVRV < 0.8: Sous-évaluation (ACHETER)
    - NUPL > 0.75: Euphorie (VENDRE)
    - NUPL < 0: Capitulation (ACHETER)
    - Funding > 0.1%/8h: Correction probable
    """

    def __init__(self, config: dict):
        """
        Initialise l'analyseur on-chain.

        Args:
            config: Configuration avec les API keys
        """
        self.config = config.get('onchain', {})
        self.enabled = self.config.get('enabled', False)
        self.glassnode_key = self.config.get('glassnode_api_key', '')
        self.coinglass_key = self.config.get('coinglass_api_key', '')

        # Seuils MVRV
        self.mvrv_thresholds = self.config.get('mvrv', {
            'extreme_euphoria': 3.5,
            'overheated': 2.4,
            'equilibrium': 1.0,
            'undervalued': 0.8
        })

        # Seuils NUPL
        self.nupl_thresholds = self.config.get('nupl', {
            'euphoria': 0.75,
            'strong_conviction': 0.50,
            'capitulation': 0.0
        })

        # Seuils Funding
        self.funding_thresholds = self.config.get('funding', {
            'extreme_long': 0.001,
            'caution': 0.0005,
            'short_squeeze': 0.0
        })

    async def get_mvrv(self, asset: str = 'BTC') -> Optional[Dict]:
        """
        Récupère le MVRV Ratio.

        MVRV = Market Value / Realized Value
        Mesure le profit non réalisé de l'ensemble du marché.

        Args:
            asset: 'BTC' ou 'ETH'

        Returns:
            Dict avec valeur et signal
        """
        if not self.enabled or not self.glassnode_key:
            return self._get_mock_mvrv()

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.glassnode.com/v1/metrics/market/mvrv"
                params = {
                    'a': asset,
                    'api_key': self.glassnode_key
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            value = data[-1].get('v', 1.0)
                            return self._interpret_mvrv(value)

        except Exception as e:
            logger.error(f"Error fetching MVRV: {e}")

        return self._get_mock_mvrv()

    def _interpret_mvrv(self, value: float) -> Dict:
        """Interprète la valeur MVRV."""
        thresholds = self.mvrv_thresholds

        if value > thresholds['extreme_euphoria']:
            signal = 'SELL_STRONG'
            description = 'Euphorie extrême - distribution probable'
        elif value > thresholds['overheated']:
            signal = 'SELL'
            description = 'Marché surchauffé - prendre profits partiels'
        elif value < thresholds['undervalued']:
            signal = 'BUY_STRONG'
            description = 'Sous-évaluation extrême - capitulation'
        elif value < thresholds['equilibrium']:
            signal = 'BUY'
            description = 'Marché sous l\'eau - zone d\'accumulation'
        else:
            signal = 'NEUTRAL'
            description = 'Zone neutre'

        return {
            'metric': 'MVRV',
            'value': round(value, 2),
            'signal': signal,
            'description': description,
            'thresholds': thresholds,
            'timestamp': datetime.now().isoformat()
        }

    def _get_mock_mvrv(self) -> Dict:
        """Retourne une valeur MVRV simulée."""
        return self._interpret_mvrv(1.5)

    async def get_nupl(self, asset: str = 'BTC') -> Optional[Dict]:
        """
        Récupère le NUPL (Net Unrealized Profit/Loss).

        NUPL = (Market Cap - Realized Cap) / Market Cap
        Identifie les phases du cycle de marché.

        Args:
            asset: 'BTC' ou 'ETH'

        Returns:
            Dict avec valeur et signal
        """
        if not self.enabled or not self.glassnode_key:
            return self._get_mock_nupl()

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.glassnode.com/v1/metrics/indicators/nupl"
                params = {
                    'a': asset,
                    'api_key': self.glassnode_key
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            value = data[-1].get('v', 0.5)
                            return self._interpret_nupl(value)

        except Exception as e:
            logger.error(f"Error fetching NUPL: {e}")

        return self._get_mock_nupl()

    def _interpret_nupl(self, value: float) -> Dict:
        """Interprète la valeur NUPL."""
        thresholds = self.nupl_thresholds

        if value > thresholds['euphoria']:
            signal = 'SELL_STRONG'
            phase = 'Euphoria'
            description = 'Euphorie - zone de distribution'
        elif value > thresholds['strong_conviction']:
            signal = 'SELL'
            phase = 'Belief'
            description = 'Conviction forte - réduire exposition'
        elif value > 0.25:
            signal = 'HOLD'
            phase = 'Optimism'
            description = 'Optimisme - conserver'
        elif value > thresholds['capitulation']:
            signal = 'BUY'
            phase = 'Hope/Fear'
            description = 'Zone de peur - opportunité d\'achat'
        else:
            signal = 'BUY_STRONG'
            phase = 'Capitulation'
            description = 'Capitulation - achat fort'

        return {
            'metric': 'NUPL',
            'value': round(value, 4),
            'signal': signal,
            'phase': phase,
            'description': description,
            'thresholds': thresholds,
            'timestamp': datetime.now().isoformat()
        }

    def _get_mock_nupl(self) -> Dict:
        """Retourne une valeur NUPL simulée."""
        return self._interpret_nupl(0.4)

    async def get_funding_rates(self, symbol: str = 'BTC') -> Optional[Dict]:
        """
        Récupère les funding rates.

        Funding rates révèlent le biais du marché:
        - > 0.1% (8h): Longs surchargés, correction probable
        - < 0%: Shorts dominants, potentiel long squeeze

        Args:
            symbol: 'BTC', 'ETH', etc.

        Returns:
            Dict avec les funding rates
        """
        if not self.enabled:
            return self._get_mock_funding()

        try:
            async with aiohttp.ClientSession() as session:
                # Using CoinGlass API for funding rates
                url = "https://open-api.coinglass.com/public/v2/funding"
                headers = {'coinglassSecret': self.coinglass_key}
                params = {'symbol': symbol}

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return self._interpret_funding(data.get('data', {}))

        except Exception as e:
            logger.error(f"Error fetching funding rates: {e}")

        return self._get_mock_funding()

    def _interpret_funding(self, data: dict) -> Dict:
        """Interprète les funding rates."""
        # Average across major exchanges
        rates = []
        for exchange_data in data.get('marginList', []):
            rate = exchange_data.get('rate', 0)
            if rate:
                rates.append(float(rate))

        avg_rate = sum(rates) / len(rates) if rates else 0
        thresholds = self.funding_thresholds

        if avg_rate > thresholds['extreme_long']:
            signal = 'BEARISH'
            description = 'Longs extrêmement surchargés - correction probable'
        elif avg_rate > thresholds['caution']:
            signal = 'CAUTION'
            description = 'Prudence sur nouveaux longs'
        elif avg_rate < thresholds['short_squeeze']:
            signal = 'BULLISH'
            description = 'Shorts dominants - potentiel squeeze'
        else:
            signal = 'NEUTRAL'
            description = 'Funding neutre'

        return {
            'metric': 'Funding Rate',
            'value': round(avg_rate * 100, 4),  # En pourcentage
            'value_8h': round(avg_rate * 100, 4),
            'signal': signal,
            'description': description,
            'thresholds': {k: v * 100 for k, v in thresholds.items()},
            'timestamp': datetime.now().isoformat()
        }

    def _get_mock_funding(self) -> Dict:
        """Retourne des funding rates simulés."""
        return {
            'metric': 'Funding Rate',
            'value': 0.01,
            'value_8h': 0.01,
            'signal': 'NEUTRAL',
            'description': 'Funding neutre (données simulées)',
            'timestamp': datetime.now().isoformat()
        }

    async def get_exchange_flows(self, asset: str = 'BTC') -> Optional[Dict]:
        """
        Récupère les flux d'exchange.

        Inflows élevés: Pression vendeuse (BEARISH)
        Outflows élevés: Accumulation (BULLISH)

        Args:
            asset: 'BTC' ou 'ETH'

        Returns:
            Dict avec les flux
        """
        if not self.enabled or not self.glassnode_key:
            return self._get_mock_flows()

        try:
            async with aiohttp.ClientSession() as session:
                # Inflows
                inflow_url = f"https://api.glassnode.com/v1/metrics/transactions/transfers_volume_to_exchanges_sum"
                outflow_url = f"https://api.glassnode.com/v1/metrics/transactions/transfers_volume_from_exchanges_sum"
                params = {'a': asset, 'api_key': self.glassnode_key}

                async with session.get(inflow_url, params=params) as resp:
                    inflow_data = await resp.json() if resp.status == 200 else []

                async with session.get(outflow_url, params=params) as resp:
                    outflow_data = await resp.json() if resp.status == 200 else []

                if inflow_data and outflow_data:
                    inflow = inflow_data[-1].get('v', 0)
                    outflow = outflow_data[-1].get('v', 0)
                    return self._interpret_flows(inflow, outflow)

        except Exception as e:
            logger.error(f"Error fetching exchange flows: {e}")

        return self._get_mock_flows()

    def _interpret_flows(self, inflow: float, outflow: float) -> Dict:
        """Interprète les flux d'exchange."""
        net_flow = inflow - outflow
        flow_ratio = inflow / outflow if outflow > 0 else 1

        if flow_ratio > 1.2:
            signal = 'BEARISH'
            description = 'Inflows dominants - pression vendeuse'
        elif flow_ratio < 0.8:
            signal = 'BULLISH'
            description = 'Outflows dominants - accumulation'
        else:
            signal = 'NEUTRAL'
            description = 'Flux équilibrés'

        return {
            'metric': 'Exchange Flows',
            'inflow': round(inflow, 2),
            'outflow': round(outflow, 2),
            'net_flow': round(net_flow, 2),
            'flow_ratio': round(flow_ratio, 2),
            'signal': signal,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }

    def _get_mock_flows(self) -> Dict:
        """Retourne des flux simulés."""
        return self._interpret_flows(1000, 1100)

    async def get_all_metrics(self, asset: str = 'BTC') -> Dict:
        """
        Récupère toutes les métriques on-chain.

        Args:
            asset: 'BTC' ou 'ETH'

        Returns:
            Dict avec toutes les métriques
        """
        mvrv = await self.get_mvrv(asset)
        nupl = await self.get_nupl(asset)
        funding = await self.get_funding_rates(asset)
        flows = await self.get_exchange_flows(asset)

        # Composite signal
        signals = [
            mvrv.get('signal', 'NEUTRAL') if mvrv else 'NEUTRAL',
            nupl.get('signal', 'NEUTRAL') if nupl else 'NEUTRAL',
            funding.get('signal', 'NEUTRAL') if funding else 'NEUTRAL',
            flows.get('signal', 'NEUTRAL') if flows else 'NEUTRAL'
        ]

        bullish_count = sum(1 for s in signals if 'BUY' in s or s == 'BULLISH')
        bearish_count = sum(1 for s in signals if 'SELL' in s or s == 'BEARISH')

        if bullish_count > bearish_count:
            composite = 'BULLISH'
        elif bearish_count > bullish_count:
            composite = 'BEARISH'
        else:
            composite = 'NEUTRAL'

        return {
            'asset': asset,
            'mvrv': mvrv,
            'nupl': nupl,
            'funding': funding,
            'exchange_flows': flows,
            'composite_signal': composite,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'timestamp': datetime.now().isoformat()
        }
