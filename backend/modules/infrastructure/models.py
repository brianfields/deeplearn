"""
Infrastructure Module - Models

No ORM models needed; infrastructure provides shared utilities and session management.
Configuration DTOs for various infrastructure services.
"""

from dataclasses import dataclass


@dataclass
class RedisConfig:
    """Redis configuration DTO."""

    url: str | None = None
    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    db: int = 0
    max_connections: int = 10
    socket_timeout: float = 5.0
    connection_timeout: float = 5.0
    health_check_interval: int = 30
