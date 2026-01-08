"""
Module WebSocket pour les mises à jour en temps réel.
"""

from fastapi import WebSocket
from typing import Dict, List, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gère les connexions WebSocket.

    Fonctionnalités:
    - Gestion des connexions/déconnexions
    - Broadcast des mises à jour
    - Souscriptions par symbole
    """

    def __init__(self):
        """Initialise le gestionnaire de connexions."""
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket):
        """
        Accepte une nouvelle connexion.

        Args:
            websocket: Instance WebSocket
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Gère une déconnexion.

        Args:
            websocket: Instance WebSocket
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """
        Envoie un message à un client spécifique.

        Args:
            message: Message à envoyer
            websocket: Client cible
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict):
        """
        Envoie un message à tous les clients connectés.

        Args:
            message: Message à diffuser
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(connection)

        # Nettoyer les connexions mortes
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_to_subscribers(self, symbol: str, message: Dict):
        """
        Envoie un message aux clients abonnés à un symbole.

        Args:
            symbol: Symbole concerné
            message: Message à envoyer
        """
        disconnected = []
        for connection, symbols in self.subscriptions.items():
            if symbol in symbols or not symbols:  # Envoyer si abonné ou si pas de filtre
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to subscriber: {e}")
                    disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    def subscribe(self, websocket: WebSocket, symbols: List[str]):
        """
        Abonne un client à des symboles.

        Args:
            websocket: Client
            symbols: Liste des symboles
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(symbols)
            logger.info(f"Client subscribed to: {symbols}")

    def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        """
        Désabonne un client de symboles.

        Args:
            websocket: Client
            symbols: Liste des symboles
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket].difference_update(symbols)


class WebSocketHandler:
    """
    Gestionnaire de messages WebSocket.

    Gère les différents types de messages:
    - subscribe: S'abonner à des symboles
    - unsubscribe: Se désabonner
    - execute_trade: Exécuter un trade
    - close_position: Fermer une position
    - ping: Vérifier la connexion
    """

    def __init__(self, manager: ConnectionManager, paper_trader=None, portfolio=None):
        """
        Initialise le handler.

        Args:
            manager: ConnectionManager instance
            paper_trader: Paper trader instance
            portfolio: Portfolio instance
        """
        self.manager = manager
        self.paper_trader = paper_trader
        self.portfolio = portfolio

    async def handle_message(self, websocket: WebSocket, data: Dict) -> Dict:
        """
        Traite un message reçu.

        Args:
            websocket: Client source
            data: Message reçu

        Returns:
            Réponse à envoyer
        """
        msg_type = data.get('type', '')

        handlers = {
            'subscribe': self._handle_subscribe,
            'unsubscribe': self._handle_unsubscribe,
            'execute_trade': self._handle_execute_trade,
            'close_position': self._handle_close_position,
            'ping': self._handle_ping,
            'get_portfolio': self._handle_get_portfolio,
            'get_positions': self._handle_get_positions
        }

        handler = handlers.get(msg_type)
        if handler:
            return await handler(websocket, data)

        return {
            'type': 'error',
            'message': f'Unknown message type: {msg_type}'
        }

    async def _handle_subscribe(self, websocket: WebSocket, data: Dict) -> Dict:
        """Gère une demande d'abonnement."""
        symbols = data.get('symbols', [])
        self.manager.subscribe(websocket, symbols)
        return {
            'type': 'subscribed',
            'symbols': list(self.manager.subscriptions.get(websocket, set()))
        }

    async def _handle_unsubscribe(self, websocket: WebSocket, data: Dict) -> Dict:
        """Gère une demande de désabonnement."""
        symbols = data.get('symbols', [])
        self.manager.unsubscribe(websocket, symbols)
        return {
            'type': 'unsubscribed',
            'symbols': symbols
        }

    async def _handle_execute_trade(self, websocket: WebSocket, data: Dict) -> Dict:
        """Gère l'exécution d'un trade."""
        if not self.paper_trader:
            return {'type': 'error', 'message': 'Paper trader not available'}

        signal = data.get('signal')
        if not signal:
            return {'type': 'error', 'message': 'No signal provided'}

        result = await self.paper_trader.execute_signal(signal)
        return {
            'type': 'trade_result',
            'result': result
        }

    async def _handle_close_position(self, websocket: WebSocket, data: Dict) -> Dict:
        """Gère la fermeture d'une position."""
        if not self.paper_trader:
            return {'type': 'error', 'message': 'Paper trader not available'}

        position_id = data.get('position_id')
        current_price = data.get('current_price')

        if not position_id or not current_price:
            return {'type': 'error', 'message': 'Missing position_id or current_price'}

        result = await self.paper_trader.close_position_manual(position_id, current_price)
        return {
            'type': 'close_result',
            'result': result
        }

    async def _handle_ping(self, websocket: WebSocket, data: Dict) -> Dict:
        """Répond à un ping."""
        return {'type': 'pong', 'timestamp': data.get('timestamp')}

    async def _handle_get_portfolio(self, websocket: WebSocket, data: Dict) -> Dict:
        """Retourne le portfolio."""
        if not self.portfolio:
            return {'type': 'error', 'message': 'Portfolio not available'}

        return {
            'type': 'portfolio',
            'data': self.portfolio.get_summary()
        }

    async def _handle_get_positions(self, websocket: WebSocket, data: Dict) -> Dict:
        """Retourne les positions."""
        if not self.portfolio:
            return {'type': 'error', 'message': 'Portfolio not available'}

        return {
            'type': 'positions',
            'data': self.portfolio.get_positions_list()
        }
