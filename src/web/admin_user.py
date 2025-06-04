from fastapi import APIRouter, Depends, status
from typing import Any, List
from uuid import UUID

from src.dependencies import db_dependency
from src.schema import PaginatedResponse
from src.schema.user import UserDisplay, UserUpdate
from src.service.user import user_service
from src.dependencies import get_current_superuser

router = APIRouter(prefix="/admin/users", tags=["Admin User Management"])


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
