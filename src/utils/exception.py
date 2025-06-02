from typing import Dict, Type, TypeVar

from fastapi import HTTPException

from .logging import logger, request_id_var

T = TypeVar("T", bound="BaseHTTPException")


class BaseHTTPException(HTTPException):
    """Base class for all HTTP exceptions with standardized error format"""

    error_code: str = "error"

    def __init__(self, detail: str = None, headers: Dict[str, str] = None):
        if detail is None:
            detail = self.__class__.__doc__ or "An error occurred"

        super().__init__(
            status_code=self.status_code,
            detail={"error": self.error_code, "message": detail},
            headers=headers,
        )

        # Store original message for logging
        self.message = detail

    @classmethod
    def with_exception(cls: Type[T], exc: Exception, prefix: str = None) -> T:
        """Create an exception instance with details from another exception"""
        message = str(exc)
        if prefix:
            message = f"{prefix}: {message}"
        return cls(detail=message)


class BadRequest(BaseHTTPException):
    """Bad request"""

    status_code = 400
    error_code = "bad_request"


class Unauthorized(BaseHTTPException):
    """Unauthorized"""

    status_code = 401
    error_code = "unauthorized"


class Forbidden(BaseHTTPException):
    """Forbidden"""

    status_code = 403
    error_code = "forbidden"


class NotFound(BaseHTTPException):
    """Not found"""

    status_code = 404
    error_code = "not_found"


class MethodNotAllowed(BaseHTTPException):
    """Method not allowed"""

    status_code = 405
    error_code = "method_not_allowed"


class Conflict(BaseHTTPException):
    """Conflict detected"""

    status_code = 409
    error_code = "conflict"


class UnprocessableEntity(BaseHTTPException):
    """Unprocessable entity"""

    status_code = 422
    error_code = "unprocessable_entity"


class TooManyRequests(BaseHTTPException):
    """Too many requests"""

    status_code = 429
    error_code = "too_many_requests"


class InternalServerError(BaseHTTPException):
    """Internal server error"""

    status_code = 500
    error_code = "internal_server_error"


class ServiceUnavailable(BaseHTTPException):
    """Service unavailable"""

    status_code = 503
    error_code = "service_unavailable"
