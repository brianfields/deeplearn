#!/usr/bin/env python3
"""
FastAPI Web Server for Conversational Learning App

Clean modular architecture using only the new /modules/ structure.
No legacy code - fresh start with proper separation of concerns.
"""

from datetime import datetime
import logging
from pathlib import Path
import sys
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.admin.routes import router as admin_router
from modules.catalog.routes import router as catalog_router
from modules.content.routes import router as content_router
from modules.content_creator.routes import router as content_creator_router
from modules.infrastructure.debug_routes import router as debug_router
from modules.infrastructure.exception_handlers import (
    setup_error_middleware,
    setup_exception_handlers,
)
from modules.infrastructure.public import DatabaseSession, infrastructure_provider
from modules.learning_coach.routes import router as learning_coach_router
from modules.learning_session.routes import router as learning_session_router
from modules.flow_engine.routes import router as flow_engine_router
from modules.task_queue.routes import router as task_queue_router
from modules.user.routes import router as user_router


# Configure enhanced logging
def setup_logging() -> None:
    """Set up enhanced logging configuration."""
    import os  # noqa: PLC0415

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    # Enhanced format for development
    if debug_mode:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Standard format for production
        logging.basicConfig(level=getattr(logging, log_level))

    # Always also write logs to backend/logs/learning_app.log so automation can tail them
    try:
        logs_dir = Path(__file__).parent / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(logs_dir / "learning_app.log", encoding="utf-8")
        if debug_mode:
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
        else:
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        file_handler.setLevel(getattr(logging, log_level))
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)

        # Capture uvicorn logs (access and error) into the same file to record 4xx/5xx
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            lg = logging.getLogger(name)
            lg.setLevel(getattr(logging, log_level))
            lg.addHandler(file_handler)
    except Exception:
        # Never fail startup due to logging file handler issues
        logger.error("Failed to set up logging file handler")
        pass

    # Set specific logger levels for better debugging
    if debug_mode:
        logging.getLogger("modules.infrastructure.error_handling").setLevel(logging.DEBUG)
        logging.getLogger("modules.flow_engine").setLevel(logging.DEBUG)


setup_logging()
logger = logging.getLogger(__name__)

# Initialize infrastructure service
infrastructure = infrastructure_provider()

# Initialize FastAPI app
app = FastAPI(
    title="Conversational Learning API",
    description="AI-powered conversational learning platform with clean modular architecture",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8081",  # This should already allow your frontend
        "http://172.16.100.219:8081",
        # For development, allow all origins to avoid IP address issues:
        "*",  # Allow all origins (DEVELOPMENT ONLY - remove for production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database dependency injection
def get_database_session() -> DatabaseSession:
    """FastAPI dependency to get database session from infrastructure module."""
    try:
        return infrastructure.get_database_session()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database service unavailable: {e}") from e


DatabaseDep = Annotated[DatabaseSession, Depends(get_database_session)]

# Set up error handling
setup_exception_handlers(app)
setup_error_middleware(app)

# Include modular routers
app.include_router(learning_session_router, tags=["Learning Sessions"])
app.include_router(catalog_router, tags=["Catalog"])
app.include_router(content_creator_router, tags=["Content Creator"])
app.include_router(content_router, tags=["Content"])
app.include_router(user_router, tags=["Users"])
app.include_router(admin_router, tags=["Admin"])
app.include_router(task_queue_router, tags=["Task Queue"])
app.include_router(flow_engine_router, tags=["Flow Engine"])
app.include_router(debug_router, tags=["Debug"])  # Only active in DEBUG mode
app.include_router(learning_coach_router, tags=["Learning Coach"])


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    try:
        # Initialize the infrastructure service
        infrastructure.initialize()

        # Validate environment
        env_status = infrastructure.validate_environment()
        if not env_status.is_valid:
            logger.warning(f"Environment validation issues: {env_status.errors}")

        logger.info("Learning API server started successfully")
        logger.info("Modular architecture: content_creator, learning_session, catalog, infrastructure")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - provides API information."""
    return {
        "message": "Lantern Room API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check() -> dict[str, str | dict[str, bool] | list[str]]:
    """Health check endpoint for the entire application."""
    env_status = infrastructure.validate_environment()

    return {
        "status": "healthy" if env_status.is_valid else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "architecture": "modular",
        "services": {
            "infrastructure": env_status.is_valid,
            "database": env_status.is_valid,
            "content_creator": True,
            "learning_session": True,
            "catalog": True,
        },
        "errors": env_status.errors if not env_status.is_valid else [],
    }


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=True,
        log_level="info",
    )
