from fastapi import APIRouter, Depends, status
from typing import Any, List
from uuid import UUID

from src.dependencies import db_dependency
from src.schema import PaginatedResponse
from src.schema.user import UserDisplay, UserUpdate
from src.service.user import user_service
from src.dependencies import (
    get_current_user,
    get_current_superuser,
)

router = APIRouter(prefix="/users", tags=["Account Mangement"])


@router.get("/current", response_model=UserDisplay)
async def read_current_user(
    current_user=Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/current", response_model=UserDisplay)
async def update_current_user(
    db: db_dependency,
    user_update: UserUpdate,
    current_user=Depends(get_current_user),
) -> Any:
    """
    Update current user.
    """
    return await user_service.update_user(db, current_user.id, user_update)


@router.get("", response_model=PaginatedResponse)
async def list_users(
    db: db_dependency,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_superuser),
) -> Any:
    """
    Retrieve users. Admin only.
    """
    return await user_service.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserDisplay)
async def read_user(
    db: db_dependency,
    user_id: UUID,
    current_user=Depends(get_current_superuser),
) -> Any:
    """
    Get user by ID. Admin only.
    """
    return await user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserDisplay)
async def update_user(
    db: db_dependency,
    user_id: UUID,
    user_update: UserUpdate,
    current_user=Depends(get_current_superuser),
) -> Any:
    """
    Update a user. Admin only.
    """
    return await user_service.update_user(db, user_id, user_update)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: db_dependency,
    user_id: UUID,
    current_user=Depends(get_current_superuser),
) -> Any:
    """
    Delete a user. Admin only.
    """
    await user_service.delete_user(db, user_id)
    return None
