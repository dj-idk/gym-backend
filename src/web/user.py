from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from src.data.database import get_db
from src.schema.user import UserRead, UserUpdate, UserList
from src.service.user import user_service
from src.utils.exceptions import NotFound, Forbidden
from src.utils.auth import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    user_update: UserUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update current user.
    """
    return await user_service.update_user(db, current_user.id, user_update)


@router.get("", response_model=List[UserList])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve users. Admin only.
    """
    return await user_service.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user by ID. Admin only.
    """
    return await user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a user. Admin only.
    """
    return await user_service.update_user(db, user_id, user_update)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a user. Admin only.
    """
    await user_service.delete_user(db, user_id)
    return None
