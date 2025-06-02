from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from typing import Any

from src.data.database import get_db
from src.schema import (
    Token,
    UserCreate,
    UserLogin,
    PasswordResetRequest,
    PasswordReset,
    EmailVerification,
)
from src.service import auth_service
from src.utils.exceptions import BadRequest, Unauthorized

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Register a new user and return access token.
    """
    return await auth_service.register_user(db, user_data)


@router.post("/login", response_model=Token)
async def login(form_data: UserLogin, db: AsyncSession = Depends(get_db)) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    return await auth_service.authenticate_user(db, form_data.email, form_data.password)


@router.post("/logout")
async def logout(token: str, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Logout user by invalidating the current token.
    """
    return await auth_service.logout(db, token)


@router.post("/password-reset/request")
async def request_password_reset(
    request_data: PasswordResetRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Request a password reset token.
    """
    return await auth_service.request_password_reset(db, request_data.email)


@router.post("/password-reset/confirm")
async def reset_password(
    reset_data: PasswordReset, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Reset password using token.
    """
    return await auth_service.reset_password(
        db, reset_data.token, reset_data.new_password
    )


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerification, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify user email with token.
    """
    return await auth_service.verify_email(db, verification_data.token)


@router.post("/refresh-token", response_model=Token)
async def refresh_token(token: str, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Refresh access token.
    """
    return await auth_service.refresh_token(db, token)
