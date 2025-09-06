"""
Unit tests for Infrastructure module.

These tests focus on infrastructure services and utilities in isolation.
They use mocks and don't require external dependencies.
"""

import os
from unittest.mock import patch

import pytest

from modules.infrastructure.module_api import InfrastructureService


class TestInfrastructureService:
    """Test cases for InfrastructureService."""

    def setup_method(self):
        """Setup for each test method."""
        # Reset service state
        InfrastructureService._connection_manager = None
        InfrastructureService._configuration = None

    def teardown_method(self):
        """Cleanup after each test method."""
        InfrastructureService.shutdown()

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "API_PORT": "8000", "LOG_LEVEL": "INFO"})
    def test_initialize_success(self):
        """Test successful initialization of infrastructure service."""
        InfrastructureService.initialize()

        # Verify configuration is loaded
        config = InfrastructureService.get_config()
        assert config.database_url == "sqlite:///:memory:"
        assert config.api_config.port == 8000
        assert config.logging_config.level == "INFO"

    def test_get_database_session_before_init_raises_error(self):
        """Test that getting database session before initialization raises error."""
        with pytest.raises(RuntimeError, match="Infrastructure service not initialized"):
            InfrastructureService.get_database_session()

    def test_get_config_before_init_raises_error(self):
        """Test that getting config before initialization raises error."""
        with pytest.raises(RuntimeError, match="Infrastructure service not initialized"):
            InfrastructureService.get_config()

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
    def test_database_session_lifecycle(self):
        """Test database session creation and cleanup."""
        InfrastructureService.initialize()

        # Get database session
        db_session = InfrastructureService.get_database_session()
        assert db_session.session is not None
        assert db_session.connection_id == "default"

        # Close session
        InfrastructureService.close_database_session(db_session)
        # Should not raise an error

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
    def test_session_context_manager(self):
        """Test database session context manager."""
        InfrastructureService.initialize()

        # Use session context manager
        with InfrastructureService.get_session_context() as session:
            assert session is not None
            # Session should be automatically cleaned up

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "DEBUG": "true"})
    def test_debug_mode_detection(self):
        """Test debug mode detection."""
        InfrastructureService.initialize()

        assert InfrastructureService.is_debug_mode() is True

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
    def test_validate_environment_success(self):
        """Test successful environment validation."""
        InfrastructureService.initialize()

        status = InfrastructureService.validate_environment()
        assert status.is_valid is True
        assert len(status.errors) == 0

    def test_validate_environment_before_init(self):
        """Test environment validation before initialization."""
        status = InfrastructureService.validate_environment()
        assert status.is_valid is False
        assert "Infrastructure service not initialized" in status.errors

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_environment_missing_config(self):
        """Test environment validation with missing configuration."""
        InfrastructureService.initialize()

        status = InfrastructureService.validate_environment()
        assert status.is_valid is False
        assert any("Missing configuration" in error for error in status.errors)

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
    def test_shutdown_cleanup(self):
        """Test that shutdown properly cleans up resources."""
        InfrastructureService.initialize()

        # Verify service is initialized
        config = InfrastructureService.get_config()
        assert config is not None

        # Shutdown
        InfrastructureService.shutdown()

        # Verify service is cleaned up
        with pytest.raises(RuntimeError):
            InfrastructureService.get_config()


class TestInfrastructureServiceIntegration:
    """Integration tests for InfrastructureService."""

    def setup_method(self):
        """Setup for each test method."""
        InfrastructureService._connection_manager = None
        InfrastructureService._configuration = None

    def teardown_method(self):
        """Cleanup after each test method."""
        InfrastructureService.shutdown()

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "API_PORT": "9000", "LOG_LEVEL": "DEBUG", "DEBUG": "true", "FEATURE_FLAG_NEW_UI": "true"})
    def test_full_configuration_loading(self):
        """Test loading complete configuration from environment."""
        InfrastructureService.initialize()

        config = InfrastructureService.get_config()

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
        assert InfrastructureService.is_debug_mode() is True
