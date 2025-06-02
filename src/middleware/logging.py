from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

from src.utils import logger, request_id_var


def get_request_id():
    """Get the current request ID or generate a new one"""
    request_id = request_id_var.get()
    if request_id is None:
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
    return request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and responses"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Set the request ID in both the context variable and request state
        request_id_var.set(request_id)
        request.state.request_id = request_id

        start_time = time.time()

        logger.bind(request_id=request_id).info(
            f"Request: {request.method} {request.url.path}"
        )

        try:
            response = await call_next(request)

            duration = time.time() - start_time

            response.headers["X-Request-ID"] = request_id

            logger.bind(request_id=request_id).info(
                f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s"
            )

            return response

        except Exception as exc:
            duration = time.time() - start_time

            logger.bind(request_id=request_id).exception(
                f"Error processing request: {request.method} {request.url.path} - Duration: {duration:.3f}s - Error: {str(exc)}"
            )

            raise
