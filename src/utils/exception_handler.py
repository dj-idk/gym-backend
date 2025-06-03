from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from .logging import logger
from .exceptions import InternalServerError, UnprocessableEntity


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers for the application"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle Pydantic validation errors from request parsing"""
        logger.warning(f"Validation error: {exc.errors()}")
        return UnprocessableEntity(detail="Invalid request parameters").as_response()

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Handle any unhandled exceptions"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

        logger.error(f"Request path: {request.url.path}")

        return InternalServerError(detail="An unexpected error occurred").as_response()
