"""
Debug routes for testing error handling (development only).
"""

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Only create debug routes in development
if os.getenv("DEBUG", "false").lower() == "true":
    router = APIRouter(prefix="/debug", tags=["Debug"])

    class TestErrorRequest(BaseModel):
        """Request model for testing error handling."""

        message: str = "Test error message"
        error_type: str = "generic"  # generic, value_error, http_error
        include_data: dict[str, Any] = {"test_key": "test_value"}

    @router.post("/error")
    async def test_error_handling(request: TestErrorRequest) -> dict[str, str]:
        """Test endpoint to trigger different types of errors."""

        if request.error_type == "value_error":
            raise ValueError(f"Test ValueError: {request.message}")
        elif request.error_type == "http_error":
            raise HTTPException(status_code=400, detail=f"Test HTTPException: {request.message}")
        else:
            # Generic exception
            raise Exception(f"Test generic exception: {request.message}")

    @router.get("/error/{error_type}")
    async def test_error_by_path(error_type: str, message: str = "Default error message") -> dict[str, str]:
        """Test endpoint with path parameters to trigger errors."""

        if error_type == "value":
            raise ValueError(f"Path-triggered ValueError: {message}")
        elif error_type == "http":
            raise HTTPException(status_code=422, detail=f"Path-triggered HTTPException: {message}")
        elif error_type == "division":
            # Trigger a ZeroDivisionError
            result = 1 / 0
            return {"result": result}
        else:
            raise Exception(f"Path-triggered generic exception: {message}")

    @router.get("/success")
    async def test_success() -> dict[str, str]:
        """Test endpoint that succeeds (for comparison)."""
        return {"message": "Success! Error handling is working correctly."}

    @router.get("/info")
    async def debug_info() -> dict[str, str]:
        """Information about the error handling system."""
        return {
            "message": "Error handling system active",
            "behavior": "Stack traces and request details are LOGGED but NOT sent to client",
            "client_gets": "Only error type, message, and timestamp",
            "logs_contain": "Full stack traces, request context, and debugging info",
        }

else:
    # Create empty router for production
    router = APIRouter()
