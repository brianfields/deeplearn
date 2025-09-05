"""
Configuration domain entities for the Infrastructure module.

This module contains the core configuration management logic.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class DatabaseConfig:
    """Configuration for database connection."""

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
    """Configuration for API settings."""

    port: int = 8000
    host: str = "0.0.0.0"
    max_retries: int = 3
    request_timeout: int = 30


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    file: str | None = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class Configuration:
    """
    Domain entity for application configuration management.

    Contains business logic for loading, validating, and managing
    application configuration from environment variables and files.
    """

    def __init__(self, env_file: str | None = None):
        """
        Initialize configuration.

        Args:
            env_file: Optional path to .env file
        """
        self.env_file = env_file or ".env"
        self.values: dict[str, Any] = {}
        self.database_config = DatabaseConfig()
        self.api_config = APIConfig()
        self.logging_config = LoggingConfig()

    def load_from_environment(self) -> None:
        """
        Load configuration from environment variables and .env files.

        Business logic for configuration loading with fallback hierarchy.
        """
        self._load_env_file()
        self._load_environment_variables()
        self._populate_config_objects()

    def _load_env_file(self) -> None:
        """Load .env file if available."""
        if not DOTENV_AVAILABLE:
            return

        env_paths_to_try = self._get_env_file_paths()

        for env_path in env_paths_to_try:
            if env_path.exists():
                load_dotenv(env_path)
                break

    def _get_env_file_paths(self) -> list[Path]:
        """
        Get potential .env file paths in order of preference.

        Business logic for .env file discovery.
        """
        paths = []

        # If PROJECT_ROOT is set, use it first
        project_root = os.getenv("PROJECT_ROOT")
        if project_root:
            paths.append(Path(project_root) / ".env")

        # Add other potential locations
        paths.extend(
            [
                Path(self.env_file),  # Current directory
                Path(__file__).parent.parent.parent / ".env",  # Module directory
                Path(__file__).parent.parent.parent.parent / ".env",  # Backend directory
                Path(__file__).parent.parent.parent.parent.parent / ".env",  # Root directory
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
        self.values["api_host"] = os.getenv("API_HOST", "0.0.0.0")
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
            host=self.values.get("api_host", "0.0.0.0"),
            max_retries=self.values.get("max_retries", 3),
            request_timeout=self.values.get("request_timeout", 30),
        )

        # Logging config
        self.logging_config = LoggingConfig(
            level=self.values.get("log_level", "INFO"),
            file=self.values.get("log_file"),
        )

    def validate_required_config(self) -> list[str]:
        """
        Validate that required configuration is present.

        Business rules for configuration validation.

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

    def get_database_url(self) -> str | None:
        """
        Get database URL for SQLAlchemy connection.

        Business logic for database URL construction.

        Returns:
            Database URL or None if not configured
        """
        if self.database_config.url:
            return self.database_config.url

        if not self.database_config.password:
            return None

        return f"postgresql://{self.database_config.user}:{self.database_config.password}@{self.database_config.host}:{self.database_config.port}/{self.database_config.name}"

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

        Business logic for debug mode determination.

        Returns:
            True if debug mode is enabled
        """
        return self.values.get("debug", False)


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""

    pass


class ConfigurationValidator:
    """
    Domain service for configuration validation.

    Contains business rules for validating configuration values.
    """

    @staticmethod
    def validate_database_config(config: DatabaseConfig) -> list[str]:
        """
        Validate database configuration.

        Args:
            config: Database configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        if config.port <= 0 or config.port > 65535:
            errors.append("Database port must be between 1 and 65535")

        if not config.name:
            errors.append("Database name is required")

        if not config.user:
            errors.append("Database user is required")

        if config.pool_size <= 0:
            errors.append("Database pool size must be positive")

        if config.max_overflow < 0:
            errors.append("Database max overflow must be non-negative")

        return errors

    @staticmethod
    def validate_api_config(config: APIConfig) -> list[str]:
        """
        Validate API configuration.

        Args:
            config: API configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        if config.port <= 0 or config.port > 65535:
            errors.append("API port must be between 1 and 65535")

        if config.max_retries < 0:
            errors.append("Max retries must be non-negative")

        if config.request_timeout <= 0:
            errors.append("Request timeout must be positive")

        return errors

    @staticmethod
    def validate_logging_config(config: LoggingConfig) -> list[str]:
        """
        Validate logging configuration.

        Args:
            config: Logging configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.level.upper() not in valid_levels:
            errors.append(f"Log level must be one of: {', '.join(valid_levels)}")

        return errors
