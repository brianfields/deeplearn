"""
Unit tests for Infrastructure module.

These tests focus on infrastructure services and utilities in isolation.
They use mocks and don't require external dependencies.
"""

import os
from unittest.mock import patch

import pytest

from modules.infrastructure.service import InfrastructureService


class TestInfrastructureService:
    """Test cases for InfrastructureService."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        self.service = InfrastructureService()

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        if hasattr(self, "service"):
            self.service.shutdown()

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "API_PORT": "8000", "LOG_LEVEL": "INFO"})
    def test_initialize_success(self) -> None:
        """Test successful initialization of infrastructure service."""
        self.service.initialize()

        # Verify configuration is loaded
        config = self.service.get_config()
        assert config.database_url == "sqlite:///:memory:"
        assert config.api_config.port == 8000
        assert config.logging_config.level == "INFO"

    def test_get_database_session_before_init_raises_error(self) -> None:
        """Test that getting database session before initialization raises error."""
        with pytest.raises(RuntimeError, match="Infrastructure service not initialized"):
            self.service.get_database_session()

    def test_get_config_before_init_raises_error(self) -> None:
        """Test that getting config before initialization raises error."""
        with pytest.raises(RuntimeError, match="Infrastructure service not initialized"):
            self.service.get_config()

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
    def test_database_session_lifecycle(self) -> None:
        """Test database session creation and cleanup."""
        self.service.initialize()

        # Get database session
        db_session = self.service.get_database_session()
        assert db_session.session is not None
        assert db_session.connection_id == "default"

        # Close session
        self.service.close_database_session(db_session)
        # Should not raise an error

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
    def test_session_context_manager(self) -> None:
        """Test database session context manager."""
        self.service.initialize()

        # Use session context manager
        with self.service.get_session_context() as session:
            assert session is not None
            # Session should be automatically cleaned up

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "DEBUG": "true"})
    def test_debug_mode_detection(self) -> None:
        """Test debug mode detection."""
        self.service.initialize()

        assert self.service.is_debug_mode() is True

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
    def test_validate_environment_success(self) -> None:
        """Test successful environment validation."""
        self.service.initialize()

        status = self.service.validate_environment()
        assert status.is_valid is True
        assert len(status.errors) == 0

    def test_validate_environment_before_init(self) -> None:
        """Test environment validation before initialization."""
        status = self.service.validate_environment()
        assert status.is_valid is False
        assert "Infrastructure service not initialized" in status.errors

    def test_validate_environment_with_invalid_database_url(self) -> None:
        """Test environment validation with invalid database configuration."""
        # Set an invalid database URL that will fail connection
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://invalid:invalid@nonexistent:5432/invalid"}, clear=True):
            self.service.initialize()

            status = self.service.validate_environment()
            assert status.is_valid is False
            assert "Database connection is not healthy" in status.errors

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
    def test_shutdown_cleanup(self) -> None:
        """Test that shutdown properly cleans up resources."""
        self.service.initialize()

        # Verify service is initialized
        config = self.service.get_config()
        assert config is not None

        # Shutdown
        self.service.shutdown()

        # Verify service is cleaned up
        with pytest.raises(RuntimeError):
            self.service.get_config()


class TestInfrastructureServiceIntegration:
    """Integration tests for InfrastructureService."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        self.service = InfrastructureService()

    def teardown_method(self) -> None:
        """Cleanup after each test method."""
        if hasattr(self, "service"):
            self.service.shutdown()

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "API_PORT": "9000", "LOG_LEVEL": "DEBUG", "DEBUG": "true", "FEATURE_FLAG_NEW_UI": "true"})
    def test_full_configuration_loading(self) -> None:
        """Test loading complete configuration from environment."""
        self.service.initialize()

        config = self.service.get_config()

        # Verify database config
        assert config.database_url == "sqlite:///:memory:"

        # Verify API config
        assert config.api_config.port == 9000

        # Verify logging config
        assert config.logging_config.level == "DEBUG"

        # Verify feature flags
        assert config.feature_flags["debug"] is True
        assert config.feature_flags["new_ui"] is True

        # Verify debug mode
        assert self.service.is_debug_mode() is True
