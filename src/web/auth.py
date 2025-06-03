from typing import Any

from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.dependencies import db_dependency
from src.schema import (
    Token,
    UserCreate,
    PasswordResetRequest,
    PasswordReset,
    EmailVerification,
)
from src.service import auth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: db_dependency) -> Any:
    """
    Register a new user and return access token.
    """
    return await auth_service.register_user(db, user_data)


@router.post("/login", response_model=Token)
async def login(
    db: db_dependency,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    return await auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )


@router.post("/logout")
async def logout(token=Depends(oauth2_scheme)) -> Any:
    """
    Logout user by invalidating the current token.
    """
    return await auth_service.logout(token)


@router.post("/password-reset/request")
async def request_password_reset(
    request_data: PasswordResetRequest, db: db_dependency
) -> Any:
    """
    Request a password reset token.
    """
    return await auth_service.request_password_reset(db, request_data.email)


@router.post("/password-reset/confirm")
async def reset_password(reset_data: PasswordReset, db: db_dependency) -> Any:
    """
    Reset password using token.
    """
    return await auth_service.reset_password(
        db, reset_data.token, reset_data.new_password
    )


# TODO: Implement password change endpoint


@router.post("/verify-email")
async def verify_email(verification_data: EmailVerification, db: db_dependency) -> Any:
    """
    Verify user email with token.
    """
    return await auth_service.verify_email(db, verification_data.token)


@router.post("/refresh-token", response_model=Token)
async def refresh_token(db: db_dependency, token=Depends(oauth2_scheme)) -> Any:
    """
    Refresh access token.
    """
    return await auth_service.refresh_token(db, token)
