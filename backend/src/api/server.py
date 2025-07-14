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
from .connection_manager import ConnectionManager
from .routes import router as api_router
from .websocket import router as websocket_router

# Import the existing learning components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
        # Import using absolute imports from the src directory
    import config.config as config
    import enhanced_conversational_learning
    import services.learning_service as learning_service_module
    import database_service
    import data_structures
    import llm_interface

    # Extract the needed classes and functions
    config_manager = config.config_manager
    setup_logging = config.setup_logging
    validate_config = config.validate_config
    get_learning_service_config = config.get_learning_service_config

    EnhancedConversationalLearningEngine = enhanced_conversational_learning.EnhancedConversationalLearningEngine
    EnhancedConversationSession = enhanced_conversational_learning.EnhancedConversationSession

    LearningService = learning_service_module.LearningService

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
app.include_router(websocket_router)

# Global services - initialized on startup
database: Optional[DatabaseService] = None
learning_service: Optional[LearningService] = None
conversation_engine: Optional[EnhancedConversationalLearningEngine] = None

# WebSocket connection manager
# Global service instances
database = None
learning_service = None
conversation_engine = None
storage = None  # For backward compatibility

manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """
    Initialize services on startup.

    This function sets up all the core services including database, learning service,
    and conversation engine. These services are made available globally to all
    endpoints and modules.
    """
    global database, learning_service, conversation_engine, storage

    # Setup logging
    setup_logging()

    # Load configuration
    config = config_manager.config

    try:
        # Initialize database service
        database = init_database_service()
        storage = database  # For backward compatibility

        # Initialize learning service
        service_config = get_learning_service_config()
        learning_service = LearningService(service_config)

        # Create LLM provider for conversation engine
        llm_provider = create_llm_provider(service_config.llm_config)

        # Initialize enhanced conversation engine
        conversation_engine = EnhancedConversationalLearningEngine(
            llm_provider,
            database  # Pass database service instead of SimpleStorage
        )

        logger.info("Conversational Learning API server started successfully")

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