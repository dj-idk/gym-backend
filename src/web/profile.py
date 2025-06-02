from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from src.data.database import get_db
from src.schema.profile import (
    ProfileCreate,
    ProfileRead,
    ProfileUpdate,
    ProgressRecordCreate,
    ProgressRecordRead,
    ProgressRecordUpdate,
    ProfilePhotoRead,
)
from src.service.profile import profile_service
from src.utils.auth import get_current_active_user
from src.utils.exceptions import NotFound

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileRead)
async def read_my_profile(
    current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user's profile.
    """
    return await profile_service.get_profile_by_user_id(db, current_user.id)


@router.post("/me", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_my_profile(
    profile_data: ProfileCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create current user's profile.
    """
    return await profile_service.create_profile(db, current_user.id, profile_data)


@router.patch("/me", response_model=ProfileRead)
async def update_my_profile(
    profile_update: ProfileUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update current user's profile.
    """
    return await profile_service.update_profile(db, current_user.id, profile_update)


# Profile Photos
@router.post("/me/photos", response_model=ProfilePhotoRead)
async def upload_profile_photo(
    file: UploadFile = File(...),
    is_primary: bool = False,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload a profile photo.
    """
    return await profile_service.add_profile_photo(
        db, current_user.id, file, is_primary
    )


@router.patch("/me/photos/{photo_id}/set-primary")
async def set_primary_photo(
    photo_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Set a photo as primary.
    """
    return await profile_service.set_primary_photo(db, current_user.id, photo_id)


@router.delete("/me/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_photo(
    photo_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a profile photo.
    """
    await profile_service.delete_profile_photo(db, current_user.id, photo_id)
    return None


# Progress Records
@router.post("/me/progress", response_model=ProgressRecordRead)
async def create_progress_record(
    progress_data: ProgressRecordCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a progress record.
    """
    return await profile_service.create_progress_record(
        db, current_user.id, progress_data
    )


@router.get("/me/progress", response_model=List[ProgressRecordRead])
async def list_progress_records(
    skip: int = 0,
    limit: int = 100,
    start_date: str = None,
    end_date: str = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List progress records with optional date filtering.
    """
    return await profile_service.get_progress_records(
        db, current_user.id, skip, limit, start_date, end_date
    )


@router.get("/me/progress/{record_id}", response_model=ProgressRecordRead)
async def get_progress_record(
    record_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific progress record.
    """
    return await profile_service.get_progress_record(db, current_user.id, record_id)


@router.patch("/me/progress/{record_id}", response_model=ProgressRecordRead)
async def update_progress_record(
    record_id: UUID,
    record_update: ProgressRecordUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a progress record.
    """
    return await profile_service.update_progress_record(
        db, current_user.id, record_id, record_update
    )


@router.delete("/me/progress/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_progress_record(
    record_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a progress record.
    """
    await profile_service.delete_progress_record(db, current_user.id, record_id)
    return None


# Progress Photos
@router.post("/me/progress-photos", response_model=ProfilePhotoRead)
async def upload_progress_photo(
    file: UploadFile = File(...),
    category: str = None,
    notes: str = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload a progress photo.
    """
    return await profile_service.add_progress_photo(
        db, current_user.id, file, category, notes
    )
