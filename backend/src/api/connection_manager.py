"""
WebSocket connection management for real-time learning conversations.

This module handles WebSocket connection lifecycle, including connecting,
disconnecting, and sending messages to individual clients.
"""

import json
import logging
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time learning conversations.

    This class handles the lifecycle of WebSocket connections, allowing
    the server to maintain connections with multiple clients and send
    personalized messages to each connected learner.

    Attributes:
        active_connections (Dict[str, WebSocket]): Maps client IDs to WebSocket connections
    """

    def __init__(self):
        """Initialize the connection manager with an empty connections dictionary."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Accept a new WebSocket connection and register it.

        Args:
            websocket (WebSocket): The WebSocket connection to accept
            client_id (str): Unique identifier for the client

        Notes:
            - Automatically accepts the WebSocket connection
            - Registers the connection for future message sending
            - Overwrites any existing connection with the same client_id
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """
        Remove a client connection from the active connections.

        Args:
            client_id (str): Unique identifier for the client to disconnect

        Notes:
            - Safely removes the connection if it exists
            - Does nothing if the client_id is not found
            - Connection cleanup is handled by FastAPI/WebSocket library
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, client_id: str):
        """
        Send a personal message to a specific connected client.

        Args:
            message (dict): The message data to send (will be JSON serialized)
            client_id (str): Unique identifier for the target client

        Notes:
            - Only sends if the client is currently connected
            - Automatically JSON serializes the message
            - Silently ignores if client is not connected
            - Does not handle WebSocket errors (caller should handle)
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
                logger.debug(f"Message sent to client {client_id}: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
                # Remove the connection if sending fails
                self.disconnect(client_id)

    def get_connection_count(self) -> int:
        """
        Get the current number of active connections.

        Returns:
            int: Number of currently active WebSocket connections
        """
        return len(self.active_connections)

    def is_connected(self, client_id: str) -> bool:
        """
        Check if a specific client is currently connected.

        Args:
            client_id (str): Unique identifier for the client

        Returns:
            bool: True if client is connected, False otherwise
        """
        return client_id in self.active_connections