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

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import the modular components
from .models import (
    StartTopicRequest,
    ChatMessage,
    LearningPathResponse,
    ConversationResponse,
    ProgressResponse
)
from .routes import router as api_router
from .content_creation_routes import router as content_creation_router

# Import the existing learning components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Import using absolute imports from the src directory
    import config.config as config
    import database_service
    import data_structures
    import llm_interface

    # Extract the needed classes and functions
    config_manager = config.config_manager
    setup_logging = config.setup_logging
    validate_config = config.validate_config

    DatabaseService = database_service.DatabaseService
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
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js frontend (multiple ports)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(content_creation_router)

# Global services - initialized on startup
database: Optional[DatabaseService] = None

# Global service instances
database = None
storage = None  # For backward compatibility


@app.on_event("startup")
async def startup_event():
    """
    Initialize services on startup.

    This function sets up the core database service for bite-sized topics.
    """
    global database, storage

    # Setup logging
    setup_logging()

    # Load configuration
    config = config_manager.config

    try:
        # Initialize database service
        database = init_database_service()
        storage = database  # For backward compatibility

        logger.info("Bite-Sized Topics API server started successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Continue without services - will return errors for API calls


if __name__ == "__main__":
    # Load configuration
    config = config_manager.config

    # Run the server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )