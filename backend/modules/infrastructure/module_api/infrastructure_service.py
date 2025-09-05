"""
Infrastructure Service - Public API for the Infrastructure module.

This module provides the thin service layer that orchestrates domain entities
and infrastructure implementations. Other modules should only access
infrastructure functionality through this service.
"""

from ..domain.entities.configuration import Configuration, DatabaseConfig
from ..domain.entities.database import DatabaseSessionManager
from ..infrastructure.database.connection_manager import ConnectionManager
from .types import AppConfig, DatabaseSession, EnvironmentStatus


class InfrastructureService:
    """
    Thin service layer for infrastructure operations.

    Provides orchestration between domain entities and infrastructure implementations.
    Contains no business logic - only coordinates calls to domain entities.
    """

    _connection_manager: ConnectionManager | None = None
    _configuration: Configuration | None = None

    @classmethod
    def initialize(cls, env_file: str | None = None) -> None:
        """
        Initialize the infrastructure service.

        Args:
            env_file: Optional path to .env file
        """
        # Initialize configuration
        cls._configuration = Configuration(env_file)
        cls._configuration.load_from_environment()

        # Initialize connection manager
        cls._connection_manager = ConnectionManager()

        # Set up default database connection if configured
        database_url = cls._configuration.get_database_url()
        if database_url:
            cls._connection_manager.set_default_connection(database_url, cls._configuration.database_config.echo)

    @classmethod
    def get_database_session(cls) -> DatabaseSession:
        """
        Get a database session for data operations.

        Returns:
            Database session wrapper

        Raises:
            RuntimeError: If infrastructure not initialized
        """
        if cls._connection_manager is None:
            raise RuntimeError("Infrastructure service not initialized. Call initialize() first.")

        connection = cls._connection_manager.get_default_connection()
        session = connection.get_session()

        return DatabaseSession(session=session, connection_id="default")

    @classmethod
    def close_database_session(cls, database_session: DatabaseSession) -> None:
        """
        Close a database session.

        Args:
            database_session: Database session to close
        """
        if cls._connection_manager is None:
            return

        connection = cls._connection_manager.get_default_connection()
        connection.close_session(database_session.session)

    @classmethod
    def get_session_context(cls):
        """
        Get a database session context manager.

        Returns:
            Database session context manager for automatic cleanup
        """
        if cls._connection_manager is None:
            raise RuntimeError("Infrastructure service not initialized. Call initialize() first.")

        connection = cls._connection_manager.get_default_connection()
        session_manager = DatabaseSessionManager(connection)
        return session_manager.create_session_context()

    @classmethod
    def get_config(cls) -> AppConfig:
        """
        Get application configuration.

        Returns:
            Application configuration

        Raises:
            RuntimeError: If infrastructure not initialized
        """
        if cls._configuration is None:
            raise RuntimeError("Infrastructure service not initialized. Call initialize() first.")

        return AppConfig(database_url=cls._configuration.get_database_url(), api_config=cls._configuration.api_config, feature_flags=cls._configuration.get_feature_flags(), logging_config=cls._configuration.logging_config)

    @classmethod
    def validate_environment(cls) -> EnvironmentStatus:
        """
        Validate infrastructure environment.

        Returns:
            Environment validation status
        """
        if cls._configuration is None:
            return EnvironmentStatus(is_valid=False, errors=["Infrastructure service not initialized"])

        errors = []

        # Validate configuration
        missing_config = cls._configuration.validate_required_config()
        if missing_config:
            errors.extend([f"Missing configuration: {config}" for config in missing_config])

        # Validate database connection
        if cls._connection_manager:
            if not cls._connection_manager.health_check():
                errors.append("Database connection is not healthy")
        else:
            errors.append("Database connection manager not initialized")

        return EnvironmentStatus(is_valid=len(errors) == 0, errors=errors)

    @classmethod
    def get_database_config(cls) -> DatabaseConfig:
        """
        Get database configuration.

        Returns:
            Database configuration
        """
        if cls._configuration is None:
            raise RuntimeError("Infrastructure service not initialized. Call initialize() first.")

        return cls._configuration.database_config

    @classmethod
    def is_debug_mode(cls) -> bool:
        """
        Check if debug mode is enabled.

        Returns:
            True if debug mode is enabled
        """
        if cls._configuration is None:
            return False

        return cls._configuration.is_debug_mode()

    @classmethod
    def shutdown(cls) -> None:
        """
        Shutdown infrastructure service and cleanup resources.
        """
        if cls._connection_manager:
            cls._connection_manager.close_all_connections()
            cls._connection_manager = None

        cls._configuration = None
