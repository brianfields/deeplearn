"""
Infrastructure Service - Use-cases for infrastructure operations.

This service provides configuration management, database session handling,
and environment validation. Returns DTOs for external consumption.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from types import TracebackType
from typing import Any, cast

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


# DTOs for external consumption
@dataclass
class DatabaseConfig:
    """Database configuration DTO."""

    url: str | None = None
    host: str = "localhost"
    port: int = 5432
    name: str = "deeplearn"
    user: str = "postgres"
    password: str | None = None
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600


@dataclass
class APIConfig:
    """API configuration DTO."""

    port: int = 8000
    host: str = "0.0.0.0"  # noqa: S104
    max_retries: int = 3
    request_timeout: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration DTO."""

    level: str = "INFO"
    file: str | None = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class DatabaseSession:
    """Database session wrapper DTO."""

    session: Session
    connection_id: str


@dataclass
class AppConfig:
    """Application configuration DTO."""

    database_url: str
    api_config: APIConfig
    feature_flags: dict[str, bool]
    logging_config: LoggingConfig


@dataclass
class EnvironmentStatus:
    """Environment validation status DTO."""

    is_valid: bool
    errors: list[str]


class InfrastructureError(Exception):
    """Base exception for infrastructure errors."""

    pass


class DatabaseConnectionError(InfrastructureError):
    """Exception raised for database connection errors."""

    pass


class ConfigurationError(InfrastructureError):
    """Exception raised for configuration errors."""

    pass


class InfrastructureService:
    """
    Infrastructure service providing configuration and database management.

    This service handles:
    - Configuration loading from environment variables and .env files
    - Database connection management and session creation
    - Environment validation
    """

    def __init__(self) -> None:
        self.engine: Engine | None = None
        self.session_factory: sessionmaker[Session] | None = None
        self.database_config = DatabaseConfig()
        self.api_config = APIConfig()
        self.logging_config = LoggingConfig()
        self.values: dict[str, Any] = {}
        self._initialized = False

    def initialize(self, env_file: str | None = None) -> None:
        """
        Initialize the infrastructure service.

        This method is idempotent - multiple calls are safe and will not
        reinitialize if already initialized.

        Args:
            env_file: Optional path to .env file
        """
        if self._initialized:
            return  # Already initialized, skip redundant initialization

        self._load_configuration(env_file)
        self._setup_database_connection()
        self._initialized = True

    def _load_configuration(self, env_file: str | None = None) -> None:
        """Load configuration from environment variables and .env files."""
        self._load_env_file(env_file or ".env")
        self._load_environment_variables()
        self._populate_config_objects()

    def _load_env_file(self, env_file: str) -> None:
        """Load .env file if available."""
        if not DOTENV_AVAILABLE:
            return

        env_paths_to_try = self._get_env_file_paths(env_file)

        for env_path in env_paths_to_try:
            if env_path.exists():
                load_dotenv(env_path)
                break

    def _get_env_file_paths(self, env_file: str) -> list[Path]:
        """Get potential .env file paths in order of preference."""
        paths = []

        # If PROJECT_ROOT is set, use it first
        project_root = os.getenv("PROJECT_ROOT")
        if project_root:
            paths.append(Path(project_root) / ".env")

        # Add other potential locations
        paths.extend(
            [
                Path(env_file),  # Current directory
                Path(__file__).parent.parent / ".env",  # Module directory
                Path(__file__).parent.parent.parent / ".env",  # Backend directory
                Path(__file__).parent.parent.parent.parent / ".env",  # Root directory
            ]
        )

        return paths

    def _load_environment_variables(self) -> None:
        """Load configuration values from environment variables."""
        # Database Configuration
        self.values["database_url"] = os.getenv("DATABASE_URL")
        self.values["database_host"] = os.getenv("DATABASE_HOST", "localhost")
        self.values["database_port"] = int(os.getenv("DATABASE_PORT", "5432"))
        self.values["database_name"] = os.getenv("DATABASE_NAME", "deeplearn")
        self.values["database_user"] = os.getenv("DATABASE_USER", "postgres")
        self.values["database_password"] = os.getenv("DATABASE_PASSWORD")
        self.values["database_echo"] = os.getenv("DATABASE_ECHO", "false").lower() == "true"

        # API Configuration
        self.values["api_port"] = int(os.getenv("API_PORT", "8000"))
        self.values["api_host"] = os.getenv("API_HOST", "0.0.0.0")  # noqa: S104
        self.values["max_retries"] = int(os.getenv("MAX_RETRIES", "3"))
        self.values["request_timeout"] = int(os.getenv("REQUEST_TIMEOUT", "30"))

        # Logging Configuration
        self.values["log_level"] = os.getenv("LOG_LEVEL", "INFO")
        self.values["log_file"] = os.getenv("LOG_FILE")
        self.values["log_format"] = os.getenv("LOG_FORMAT", "json")

        # Feature flags
        self.values["debug"] = os.getenv("DEBUG", "false").lower() == "true"
        self.values["feature_flag_new_ui"] = os.getenv("FEATURE_FLAG_NEW_UI", "false").lower() == "true"

    def _populate_config_objects(self) -> None:
        """Populate typed configuration objects from loaded values."""
        # Database config
        self.database_config = DatabaseConfig(
            url=self.values.get("database_url"),
            host=self.values.get("database_host", "localhost"),
            port=self.values.get("database_port", 5432),
            name=self.values.get("database_name", "deeplearn"),
            user=self.values.get("database_user", "postgres"),
            password=self.values.get("database_password"),
            echo=self.values.get("database_echo", False),
        )

        # API config
        self.api_config = APIConfig(
            port=self.values.get("api_port", 8000),
            host=self.values.get("api_host", "0.0.0.0"),  # noqa: S104
            max_retries=self.values.get("max_retries", 3),
            request_timeout=self.values.get("request_timeout", 30),
        )

        # Logging config
        self.logging_config = LoggingConfig(
            level=self.values.get("log_level", "INFO"),
            file=self.values.get("log_file"),
        )

    def _setup_database_connection(self) -> None:
        """Set up database connection and session factory."""
        database_url = self.get_database_url()
        if not database_url:
            return  # No database configuration

        try:
            # Configure engine parameters based on database type
            engine_kwargs: dict[str, Any] = {
                "echo": self.database_config.echo,
            }

            # Only add pooling parameters for databases that support them
            if not database_url.startswith("sqlite"):
                engine_kwargs["pool_size"] = self.database_config.pool_size
                engine_kwargs["max_overflow"] = self.database_config.max_overflow
                engine_kwargs["pool_recycle"] = self.database_config.pool_recycle

            self.engine = create_engine(database_url, **engine_kwargs)
            self.session_factory = sessionmaker(bind=self.engine, class_=Session, autoflush=False, autocommit=False)

        except SQLAlchemyError as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e

    def get_database_url(self) -> str | None:
        """
        Get database URL for SQLAlchemy connection.

        Returns:
            Database URL or None if not configured
        """
        if self.database_config.url:
            return self.database_config.url

        if not self.database_config.password:
            return None

        return f"postgresql://{self.database_config.user}:{self.database_config.password}@{self.database_config.host}:{self.database_config.port}/{self.database_config.name}"

    def get_database_session(self) -> DatabaseSession:
        """
        Get a database session for data operations.

        Returns:
            Database session wrapper

        Raises:
            RuntimeError: If infrastructure not initialized
            DatabaseConnectionError: If no database connection available
        """
        if not self._initialized:
            raise RuntimeError("Infrastructure service not initialized. Call initialize() first.")

        if self.session_factory is None:
            raise DatabaseConnectionError("Database not connected. No database URL configured.")

        session = self.session_factory()
        return DatabaseSession(session=session, connection_id="default")

    def close_database_session(self, database_session: DatabaseSession) -> None:
        """
        Close a database session.

        Args:
            database_session: Database session to close
        """
        if database_session.session:
            database_session.session.close()

    def get_session_context(self) -> "DatabaseSessionContext":
        """
        Get a database session context manager.

        Returns:
            Database session context manager for automatic cleanup
        """
        if not self._initialized:
            raise RuntimeError("Infrastructure service not initialized. Call initialize() first.")

        if self.session_factory is None:
            raise DatabaseConnectionError("Database not connected. No database URL configured.")

        return DatabaseSessionContext(self.session_factory)

    def get_config(self) -> AppConfig:
        """
        Get application configuration.

        Returns:
            Application configuration

        Raises:
            RuntimeError: If infrastructure not initialized
        """
        if not self._initialized:
            raise RuntimeError("Infrastructure service not initialized. Call initialize() first.")

        database_url = self.get_database_url()
        if not database_url:
            raise ConfigurationError("Database URL not configured")

        return AppConfig(database_url=database_url, api_config=self.api_config, feature_flags=self.get_feature_flags(), logging_config=self.logging_config)

    def get_feature_flags(self) -> dict[str, bool]:
        """
        Get feature flags configuration.

        Returns:
            Dictionary of feature flags
        """
        return {
            "debug": self.values.get("debug", False),
            "new_ui": self.values.get("feature_flag_new_ui", False),
        }

    def is_debug_mode(self) -> bool:
        """
        Check if debug mode is enabled.

        Returns:
            True if debug mode is enabled
        """
        return cast(bool, self.values.get("debug", False))

    def validate_environment(self) -> EnvironmentStatus:
        """
        Validate infrastructure environment.

        Returns:
            Environment validation status
        """
        if not self._initialized:
            return EnvironmentStatus(is_valid=False, errors=["Infrastructure service not initialized"])

        errors = []

        # Validate configuration
        missing_config = self._validate_required_config()
        if missing_config:
            errors.extend([f"Missing configuration: {config}" for config in missing_config])

        # Validate database connection
        if self.engine:
            if not self._health_check():
                errors.append("Database connection is not healthy")
        else:
            errors.append("Database connection not initialized")

        return EnvironmentStatus(is_valid=len(errors) == 0, errors=errors)

    def _validate_required_config(self) -> list[str]:
        """
        Validate that required configuration is present.

        Returns:
            List of missing required configuration keys
        """
        required = ["database_url"]
        missing = []

        for key in required:
            if key == "database_url":
                # Database URL can be constructed from components
                if not self.get_database_url():
                    missing.append("database_url or database connection components")
            elif not self.values.get(key):
                missing.append(key)

        return missing

    def _health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        if self.engine is None:
            return False

        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def get_database_config(self) -> DatabaseConfig:
        """
        Get database configuration.

        Returns:
            Database configuration
        """
        if not self._initialized:
            raise RuntimeError("Infrastructure service not initialized. Call initialize() first.")

        return self.database_config

    def shutdown(self) -> None:
        """
        Shutdown infrastructure service and cleanup resources.
        """
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.session_factory = None

        self._initialized = False


class DatabaseSessionContext:
    """
    Context manager for database sessions.

    Handles automatic session creation, commit/rollback, and cleanup.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """
        Initialize session context.

        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> Session:
        """
        Enter session context and create session.

        Returns:
            Database session
        """
        self.session = self.session_factory()
        return self.session

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
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
                self.session.close()
