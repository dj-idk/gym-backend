from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from src.data.database import get_db
from src.schema.profile import (
    ProfileCreate,
    ProfileDisplay,
    ProfileUpdate,
)
from src.service.profile import profile_service
from src.dependencies import get_current_user

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/current", response_model=ProfileDisplay)
async def read_my_profile(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user's profile.
    """
    return await profile_service.get_profile_by_user_id(db, current_user.id)


@router.post(
    "/current", response_model=ProfileDisplay, status_code=status.HTTP_201_CREATED
)
async def create_my_profile(
    profile_data: ProfileCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create current user's profile.
    """
    return await profile_service.create_profile(db, current_user.id, profile_data)


@router.patch("/current", response_model=ProfileDisplay)
async def update_my_profile(
    profile_update: ProfileUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update current user's profile.
    """
    return await profile_service.update_profile(db, current_user.id, profile_update)


# Profile Photos
@router.post("/current/photos", response_model=ProfilePhotoRead)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload a profile photo.
    """
    return await profile_service.add_profile_photo(db, current_user.id, file)


@router.delete("/current/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_photo(
    photo_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a profile photo.
    """
    await profile_service.delete_profile_photo(db, current_user.id, photo_id)
    return None
