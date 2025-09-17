"""
FastAPI exception handlers for comprehensive error handling.
"""

from collections.abc import Callable
import logging

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .error_handling import create_error_response

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Set up all exception handlers for the FastAPI application."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with logging."""

        # Log HTTP exceptions for monitoring (but not full stack traces for expected errors)
        log_full_context = exc.status_code >= 500  # Only log full context for server errors

        return await create_error_response(request=request, exc=exc, status_code=exc.status_code, log_full_context=log_full_context)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors (422 responses)."""

        # Log detailed validation errors
        logger.warning(f"Validation error in {request.method} {request.url.path}", extra={"validation_errors": exc.errors(), "request_body": exc.body, "method": request.method, "path": request.url.path, "query_params": dict(request.query_params)})

        return await create_error_response(request=request, exc=exc, status_code=422, log_full_context=True)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError exceptions (usually validation errors)."""

        return await create_error_response(
            request=request,
            exc=exc,
            status_code=400,
            log_full_context=True,  # Log full context for debugging validation issues
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other unhandled exceptions."""

        # Always log full context for unhandled exceptions
        return await create_error_response(
            request=request,
            exc=exc,
            status_code=500,
            log_full_context=True,  # Always log full context for unexpected errors
        )


def setup_error_middleware(app: FastAPI) -> None:
    """Set up error handling middleware."""

    @app.middleware("http")
    async def error_logging_middleware(request: Request, call_next: Callable) -> Response:
        """Middleware to catch and log errors that slip through route handlers."""
        try:
            response = await call_next(request)

            # Log 4xx and 5xx responses for monitoring
            if response.status_code >= 400:
                logger.warning(
                    f"HTTP {response.status_code} response for {request.method} {request.url.path}", extra={"status_code": response.status_code, "method": request.method, "path": request.url.path, "query_params": dict(request.query_params)}
                )

            return response

        except Exception as exc:
            # This catches exceptions that occur in middleware or other places
            # not handled by the route exception handlers
            logger.error(f"Middleware caught unhandled exception: {exc}", exc_info=True)

            return await create_error_response(
                request=request,
                exc=exc,
                status_code=500,
                log_full_context=True,  # Always log full context for middleware errors
            )
