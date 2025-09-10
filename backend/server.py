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

from modules.content_creator.routes import router as content_creator_router
from modules.infrastructure.public import DatabaseSession, infrastructure_provider
from modules.learning_session.routes import router as learning_session_router
from modules.lesson_catalog.routes import router as lesson_catalog_router

# Configure logging
logging.basicConfig(level=logging.INFO)
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

# Include modular routers
app.include_router(content_creator_router, tags=["Content Creation"])
app.include_router(learning_session_router, tags=["Learning Sessions"])
app.include_router(lesson_catalog_router, tags=["Lesson Catalog"])


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
        logger.info("Modular architecture: content_creator, learning_session, lesson_catalog, infrastructure")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


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
            "lesson_catalog": True,
        },
        "errors": env_status.errors if not env_status.is_valid else [],
    }


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
