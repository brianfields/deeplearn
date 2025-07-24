#!/usr/bin/env python3
"""
FastAPI Web Server for Conversational Learning App

This server exposes the CLI functionality as REST APIs and WebSocket connections
for real-time conversational learning.

The server is organized into several modules:
- models.py: Pydantic request/response models
- connection_manager.py: WebSocket connection management
- routes.py: HTTP REST API endpoints
- websocket.py: WebSocket endpoint and helpers
- server.py: Main application, startup, and configuration
"""

import logging
from pathlib import Path

# Import the existing learning components
import sys
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import config

if TYPE_CHECKING:
    pass

from .content_creation_routes import router as content_creation_router
from .learning_routes import router as api_router

# Import the modular components

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Import modules but defer config loading to startup event
    import data_structures
    import database_service

    # Import DatabaseService properly for type checking
    import llm_interface

    get_database_service = database_service.get_database_service
    init_database_service = database_service.init_database_service

    ProgressStatus = data_structures.ProgressStatus
    MessageRole = llm_interface.MessageRole
    create_llm_provider = llm_interface.create_llm_provider

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the backend directory and have installed dependencies")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Conversational Learning API",
    description="AI-powered conversational learning platform",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8081",
    ],  # Next.js frontend (multiple ports)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)  # type: ignore[has-type]
app.include_router(content_creation_router)


@app.on_event("startup")
async def startup_event() -> None:
    """
    Initialize services on startup.

    This function sets up the core database service for bite-sized topics.
    """
    # Import config module here after environment is set up

    setup_logging = config.setup_logging

    # Setup logging
    setup_logging()

    try:
        # Initialize database service
        init_database_service()

        logger.info("Bite-Sized Topics API server started successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Continue without services - will return errors for API calls


if __name__ == "__main__":
    # Load configuration

    # Run the server
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")  # noqa: S104
