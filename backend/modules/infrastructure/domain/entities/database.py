"""
Database domain entities for the Infrastructure module.

This module contains the core database connection and session management logic.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


class DatabaseConnection:
    """
    Domain entity for managing database connections.

    Contains the business logic for database connection management,
    session creation, and connection validation.
    """

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL
            echo: Whether to echo SQL statements for debugging
        """
        self.database_url = database_url
        self.echo = echo
        self.engine: Engine | None = None
        self.session_factory: sessionmaker | None = None

    def connect(self) -> None:
        """
        Establish database connection and create session factory.

        Business logic for creating the SQLAlchemy engine with appropriate
        connection pooling and configuration.
        """
        if self.engine is not None:
            return  # Already connected

        try:
            # Configure engine parameters based on database type
            engine_kwargs = {
                "echo": self.echo,
            }

            # Only add pooling parameters for databases that support them
            if not self.database_url.startswith("sqlite"):
                engine_kwargs.update(
                    {
                        "pool_size": 5,
                        "max_overflow": 10,
                        "pool_recycle": 3600,
                    }
                )

            self.engine = create_engine(self.database_url, **engine_kwargs)

            self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        except SQLAlchemyError as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e

    def validate_connection(self) -> bool:
        """
        Validate that the database connection is working.

        Business logic for testing database connectivity.

        Returns:
            True if connection is valid, False otherwise
        """
        if self.engine is None:
            return False

        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def get_session(self) -> Session:
        """
        Create a new database session.

        Business logic for session creation with proper configuration.

        Returns:
            New SQLAlchemy session

        Raises:
            DatabaseConnectionError: If not connected to database
        """
        if self.session_factory is None:
            raise DatabaseConnectionError("Database not connected. Call connect() first.")

        return self.session_factory()

    def close_session(self, session: Session) -> None:
        """
        Close a database session.

        Business logic for proper session cleanup.

        Args:
            session: SQLAlchemy session to close
        """
        if session:
            session.close()

    def disconnect(self) -> None:
        """
        Disconnect from database and cleanup resources.

        Business logic for proper connection cleanup.
        """
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.session_factory = None


class DatabaseConnectionError(Exception):
    """Exception raised for database connection errors."""

    pass


class DatabaseSessionManager:
    """
    Domain entity for managing database session lifecycle.

    Provides context management and session lifecycle business logic.
    """

    def __init__(self, connection: DatabaseConnection):
        """
        Initialize session manager.

        Args:
            connection: Database connection instance
        """
        self.connection = connection

    def create_session_context(self):
        """
        Create a session context manager.

        Business logic for session lifecycle management with automatic cleanup.
        """
        return DatabaseSessionContext(self.connection)


class DatabaseSessionContext:
    """
    Context manager for database sessions.

    Handles automatic session creation, commit/rollback, and cleanup.
    """

    def __init__(self, connection: DatabaseConnection):
        """
        Initialize session context.

        Args:
            connection: Database connection instance
        """
        self.connection = connection
        self.session: Session | None = None

    def __enter__(self) -> Session:
        """
        Enter session context and create session.

        Returns:
            Database session
        """
        self.session = self.connection.get_session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit session context with proper cleanup.

        Handles commit/rollback based on whether an exception occurred.
        """
        if self.session:
            try:
                if exc_type is not None:
                    # Exception occurred, rollback
                    self.session.rollback()
                else:
                    # No exception, commit
                    self.session.commit()
            except SQLAlchemyError:
                # Error during commit/rollback, ensure rollback
                self.session.rollback()
                raise
            finally:
                # Always close session
                self.connection.close_session(self.session)
