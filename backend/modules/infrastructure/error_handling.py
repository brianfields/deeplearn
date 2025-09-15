"""
Error handling utilities for FastAPI application.

Provides comprehensive error logging with stack traces and request context.
"""

from datetime import datetime
import json
import logging
import traceback
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorContext:
    """Utility class for extracting request context."""

    @staticmethod
    async def extract_request_context(request: Request, include_body: bool = True) -> dict[str, Any]:
        """Extract comprehensive request context for error logging."""
        context = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                # Filter out sensitive headers
                k: v
                for k, v in request.headers.items()
                if k.lower() not in ["authorization", "cookie", "x-api-key"]
            },
            "client": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None,
            },
        }

        if include_body:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON first
                    try:
                        context["body"] = json.loads(body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Fallback to string representation
                        context["body"] = body.decode(errors="replace")
                else:
                    context["body"] = None
            except Exception as e:
                context["body"] = f"Error reading body: {e!s}"

        return context


async def create_error_response(request: Request, exc: Exception, status_code: int = 500, log_full_context: bool = True) -> JSONResponse:
    """Create a secure error response with comprehensive logging."""

    error_type = exc.__class__.__name__
    message = str(exc)
    timestamp = datetime.utcnow().isoformat()

    # Always extract full context for logging
    stack_trace = None
    request_context = None

    if log_full_context:
        # Extract stack trace for logging only
        stack_trace = traceback.format_exc().splitlines()

        # Extract request context for logging only
        try:
            request_context = await ErrorContext.extract_request_context(request)
        except Exception as context_error:
            logger.warning(f"Failed to extract request context: {context_error}")
            request_context = {"error": "Failed to extract request context"}

    # Log the error with full context (NEVER sent to client)
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}",
        extra={
            "error_type": error_type,
            "error_message": message,
            "request_context": request_context,
            "stack_trace": stack_trace,
            "status_code": status_code,
        },
        exc_info=True,
    )

    # Create secure client response (NO stack traces or sensitive info)
    client_response = {"error": error_type, "message": message, "timestamp": timestamp}

    # Add status code for HTTP errors
    if isinstance(exc, HTTPException):
        client_response["status_code"] = str(exc.status_code)

    return JSONResponse(status_code=status_code, content=client_response)
