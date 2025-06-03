from typing import Optional, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.config.config import settings
from src.data.user import User
from src.service import auth_service
from src.schema import TokenPayload, UserDisplay
from .db import db_dependency

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    db: db_dependency, token: str = Depends(oauth2_scheme)
) -> User:
    """
    Validate and decode the JWT token to get the current user.

    Args:
        token: JWT token from the Authorization header
        db: Database session

    Returns:
        The current authenticated user

    Raises:
        HTTPException: If the token is invalid or the user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        # Check if token has expired
        if token_data.exp is None:
            raise credentials_exception

        user_id: Optional[UUID] = token_data.sub
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get the user from the database
    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception

    return user


current_user_dependency = Annotated[UserDisplay, Depends(get_current_user)]
