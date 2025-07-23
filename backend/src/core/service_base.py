"""
Base classes for service modules.

This module provides the foundation for all service classes used across
the learning system modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import Any

from src.core.llm_client import LLMClient
from src.llm_interface import LLMConfig


@dataclass
class ServiceConfig:
    """Base configuration for services"""

    llm_config: LLMConfig
    cache_enabled: bool = True
    retry_attempts: int = 3
    timeout_seconds: int = 30
    log_level: str = "INFO"


class ModuleService(ABC):
    """
    Abstract base class for module services.

    Each module should have a main service class that inherits from this
    to provide consistent interfaces and shared functionality.
    """

    def __init__(self, config: ServiceConfig, llm_client: "LLMClient") -> None:
        self.config = config
        self.llm_client = llm_client
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging for the service"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

    async def health_check(self) -> dict[str, Any]:
        """
        Basic health check for the service.

        Returns:
            Dictionary containing health status
        """
        return {
            "service": self.__class__.__name__,
            "status": "healthy",
            "config": {
                "cache_enabled": self.config.cache_enabled,
                "retry_attempts": self.config.retry_attempts,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }

    def get_service_name(self) -> str:
        """Get the name of this service"""
        return self.__class__.__name__

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service. Must be implemented by subclasses."""
        pass


class ModuleServiceError(Exception):
    """Base exception for module service errors"""

    def __init__(self, message: str, service_name: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.service_name = service_name
        self.original_error = original_error


class ServiceFactory:
    """Factory for creating service instances with proper configuration"""

    @staticmethod
    def create_service_config(
        llm_config: LLMConfig,
        cache_enabled: bool = True,
        retry_attempts: int = 3,
        timeout_seconds: int = 30,
        log_level: str = "INFO",
    ) -> ServiceConfig:
        """Create a service configuration"""
        return ServiceConfig(
            llm_config=llm_config,
            cache_enabled=cache_enabled,
            retry_attempts=retry_attempts,
            timeout_seconds=timeout_seconds,
            log_level=log_level,
        )
