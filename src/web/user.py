from typing import Any

from fastapi import APIRouter, Query, Body

from src.dependencies import db_dependency
from src.schema.user import (
    UserDisplay,
    UserUpdate,
    UserUpdateResponse,
    EmailVerificationResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
)
from src.service.user import user_service
from src.dependencies import current_user_dependency

router = APIRouter(prefix="/users", tags=["Account Mangement"])


@router.get("/current", response_model=UserDisplay)
async def read_current_user(
    current_user: current_user_dependency,
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/current", response_model=UserUpdateResponse)
async def update_current_user(
    db: db_dependency,
    current_user: current_user_dependency,
    user_update: UserUpdate,
) -> Any:
    """
    Update current user.
    """
    return await user_service.update_user(db, current_user.id, user_update)


@router.get("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    db: db_dependency,
    token: str = Query(..., description="Email verification token"),
) -> Any:
    """
    Verify user email with the provided token.

    This endpoint is used to confirm a user's email address after they've requested
    an email change or during the registration process.
    """

    result = await user_service.verify_email(db, token)
    return result


@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    db: db_dependency,
    current_user: current_user_dependency,
    password_data: PasswordChangeRequest = Body(...),
) -> Any:
    """
    Change the current user's password.

    Requires the current password for verification and the new password to set.
    """
    result = await user_service.change_password(
        db, current_user.id, password_data.current_password, password_data.new_password
    )
    return result
