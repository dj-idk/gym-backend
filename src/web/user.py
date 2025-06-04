from typing import Any

from fastapi import APIRouter

from src.dependencies import db_dependency
from src.schema.user import UserDisplay, UserUpdate, UserUpdateResponse
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
