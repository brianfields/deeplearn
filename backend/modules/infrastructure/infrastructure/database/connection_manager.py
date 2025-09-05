"""
Database connection manager implementation.

This module provides the technical implementation for database connection management.
"""

from sqlalchemy.engine import Engine

from ...domain.entities.database import DatabaseConnection, DatabaseConnectionError


class ConnectionManager:
    """
    Infrastructure implementation for managing database connections.

    Handles connection pooling, multiple database support, and connection lifecycle.
    """

    def __init__(self):
        """Initialize connection manager."""
        self.connections: dict[str, DatabaseConnection] = {}
        self.default_connection_name = "default"

    def add_connection(self, name: str, database_url: str, echo: bool = False) -> DatabaseConnection:
        """
        Add a new database connection.

        Args:
            name: Connection name identifier
            database_url: SQLAlchemy database URL
            echo: Whether to echo SQL statements

        Returns:
            Database connection instance

        Raises:
            DatabaseConnectionError: If connection already exists
        """
        if name in self.connections:
            raise DatabaseConnectionError(f"Connection '{name}' already exists")

        connection = DatabaseConnection(database_url, echo)
        connection.connect()

        self.connections[name] = connection
        return connection

    def get_connection(self, name: str | None = None) -> DatabaseConnection:
        """
        Get database connection by name.

        Args:
            name: Connection name, defaults to default connection

        Returns:
            Database connection instance

        Raises:
            DatabaseConnectionError: If connection not found
        """
        connection_name = name or self.default_connection_name

        if connection_name not in self.connections:
            raise DatabaseConnectionError(f"Connection '{connection_name}' not found")

        return self.connections[connection_name]

    def remove_connection(self, name: str) -> None:
        """
        Remove and disconnect a database connection.

        Args:
            name: Connection name to remove
        """
        if name in self.connections:
            connection = self.connections[name]
            connection.disconnect()
            del self.connections[name]

    def get_default_connection(self) -> DatabaseConnection:
        """
        Get the default database connection.

        Returns:
            Default database connection

        Raises:
            DatabaseConnectionError: If no default connection exists
        """
        return self.get_connection(self.default_connection_name)

    def set_default_connection(self, database_url: str, echo: bool = False) -> DatabaseConnection:
        """
        Set up the default database connection.

        Args:
            database_url: SQLAlchemy database URL
            echo: Whether to echo SQL statements

        Returns:
            Default database connection
        """
        # Remove existing default connection if it exists
        if self.default_connection_name in self.connections:
            self.remove_connection(self.default_connection_name)

        return self.add_connection(self.default_connection_name, database_url, echo)

    def close_all_connections(self) -> None:
        """Close all database connections."""
        for name in list(self.connections.keys()):
            self.remove_connection(name)

    def health_check(self, name: str | None = None) -> bool:
        """
        Check if database connection is healthy.

        Args:
            name: Connection name to check, defaults to default connection

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            connection = self.get_connection(name)
            return connection.validate_connection()
        except DatabaseConnectionError:
            return False

    def get_engine(self, name: str | None = None) -> Engine:
        """
        Get SQLAlchemy engine for a connection.

        Args:
            name: Connection name, defaults to default connection

        Returns:
            SQLAlchemy engine

        Raises:
            DatabaseConnectionError: If connection not found or not connected
        """
        connection = self.get_connection(name)

        if connection.engine is None:
            raise DatabaseConnectionError(f"Connection '{name or self.default_connection_name}' not connected")

        return connection.engine
