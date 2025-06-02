import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt

from src.config import settings
from src.utils import logger, InternalServerError

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
TOKEN_COOKIE_NAME = settings.TOKEN_COOKIE_NAME
CSRF_TOKEN_SECRET = settings.CSRF_TOKEN_SECRET


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a JWT access token."""
    try:
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode = {**data, "exp": expire, "jti": str(uuid.uuid4())}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise InternalServerError(
            "An unexpected error occurred while creating access token"
        )
