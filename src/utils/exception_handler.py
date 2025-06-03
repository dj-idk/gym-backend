from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError

from .logging import logger
from .exceptions import InternalServerError, UnprocessableEntity


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers for the application"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle Pydantic validation errors from request parsing"""
        logger.warning(f"Validation error: {str(exc)}")
        return UnprocessableEntity(
            detail=f"Invalid request parameters: {str(exc)}"
        ).as_response()

    @app.exception_handler(ResponseValidationError)
    async def response_validation_exception_handler(
        request: Request, exc: ResponseValidationError
    ):
        """Handle Pydantic validation errors in response"""
        logger.error(f"Response validation error: {str(exc)}")
        return InternalServerError(
            detail="The server returned an invalid response"
        ).as_response()

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Handle any unhandled exceptions"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        logger.error(f"Request path: {request.url.path}")
        return InternalServerError(detail="An unexpected error occurred").as_response()
