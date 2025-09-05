"""
Environment configuration loader implementation.

This module provides the technical implementation for loading configuration
from various sources including environment variables and configuration files.
"""

import json
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from ...domain.entities.configuration import ConfigurationError


class EnvironmentLoader:
    """
    Infrastructure implementation for loading configuration from environment.

    Handles loading from .env files, environment variables, and configuration files.
    """

    @staticmethod
    def load_config(env_file: str | None = None) -> dict[str, Any]:
        """
        Load configuration from environment.

        Args:
            env_file: Optional path to .env file

        Returns:
            Dictionary of configuration values
        """
        config_dict = {}

        # Load .env file if available
        if DOTENV_AVAILABLE and env_file:
            EnvironmentLoader._load_dotenv_file(env_file)

        # Load from environment variables
        config_dict.update(EnvironmentLoader._load_from_environment())

        return config_dict

    @staticmethod
    def _load_dotenv_file(env_file: str) -> None:
        """Load .env file if it exists."""
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)

    @staticmethod
    def _load_from_environment() -> dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # Database Configuration
            "database": {
                "url": os.getenv("DATABASE_URL"),
                "host": os.getenv("DATABASE_HOST", "localhost"),
                "port": int(os.getenv("DATABASE_PORT", "5432")),
                "name": os.getenv("DATABASE_NAME", "deeplearn"),
                "user": os.getenv("DATABASE_USER", "postgres"),
                "password": os.getenv("DATABASE_PASSWORD"),
                "echo": os.getenv("DATABASE_ECHO", "false").lower() == "true",
                "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            },
            # API Configuration
            "api": {
                "port": int(os.getenv("API_PORT", "8000")),
                "host": os.getenv("API_HOST", "0.0.0.0"),
                "max_retries": int(os.getenv("MAX_RETRIES", "3")),
                "request_timeout": int(os.getenv("REQUEST_TIMEOUT", "30")),
            },
            # Logging Configuration
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "file": os.getenv("LOG_FILE"),
                "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            },
            # Feature Flags
            "feature_flags": {
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "new_ui": os.getenv("FEATURE_FLAG_NEW_UI", "false").lower() == "true",
            },
        }


class ConfigurationFileLoader:
    """
    Infrastructure implementation for loading configuration from files.

    Supports JSON, YAML, and other configuration file formats.
    """

    @staticmethod
    def load_json_config(file_path: str) -> dict[str, Any]:
        """
        Load configuration from JSON file.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        try:
            with open(file_path) as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration file {file_path}: {e}")

    @staticmethod
    def save_json_config(config: dict[str, Any], file_path: str) -> None:
        """
        Save configuration to JSON file.

        Args:
            config: Configuration dictionary to save
            file_path: Path to save JSON configuration file

        Raises:
            ConfigurationError: If file cannot be saved
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                json.dump(config, f, indent=2, default=str)
        except Exception as e:
            raise ConfigurationError(f"Error saving configuration file {file_path}: {e}")


class ConfigurationMerger:
    """
    Infrastructure utility for merging configuration from multiple sources.

    Handles precedence and merging logic for configuration values.
    """

    @staticmethod
    def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
        """
        Merge multiple configuration dictionaries.

        Later configurations take precedence over earlier ones.

        Args:
            *configs: Configuration dictionaries to merge

        Returns:
            Merged configuration dictionary
        """
        merged = {}

        for config in configs:
            merged = ConfigurationMerger._deep_merge(merged, config)

        return merged

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        Deep merge two configuration dictionaries.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            Merged configuration dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigurationMerger._deep_merge(result[key], value)
            else:
                result[key] = value

        return result


class EnvironmentVariableExpander:
    """
    Infrastructure utility for expanding environment variables in configuration values.

    Supports ${VAR_NAME} and ${VAR_NAME:-default_value} syntax.
    """

    @staticmethod
    def expand_variables(config: dict[str, Any]) -> dict[str, Any]:
        """
        Expand environment variables in configuration values.

        Args:
            config: Configuration dictionary with potential variables

        Returns:
            Configuration dictionary with expanded variables
        """
        expanded = {}

        for key, value in config.items():
            if isinstance(value, dict):
                expanded[key] = EnvironmentVariableExpander.expand_variables(value)
            elif isinstance(value, str):
                expanded[key] = EnvironmentVariableExpander._expand_string(value)
            else:
                expanded[key] = value

        return expanded

    @staticmethod
    def _expand_string(value: str) -> str:
        """
        Expand environment variables in a string value.

        Args:
            value: String value that may contain variables

        Returns:
            String with expanded variables
        """
        # Simple implementation - can be enhanced for more complex syntax
        return os.path.expandvars(value)
