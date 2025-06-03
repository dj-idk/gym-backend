from typing import Any

from fastapi import APIRouter, status, UploadFile, File, Response

from src.schema.profile import ProfileDisplay, ProfileUpdate, ProfilePhotoDisplay
from src.service.profile import profile_service
from src.utils.exceptions import NotFound
from src.dependencies import current_user_dependency, db_dependency

router = APIRouter(prefix="/profiles", tags=["Profile Management"])


@router.get("/current", response_model=ProfileDisplay)
async def read_my_profile(
    current_user: current_user_dependency, db: db_dependency
) -> ProfileDisplay:
    """
    Get current user's profile.
    """
    profile = await profile_service.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise NotFound("Profiel not found. Please create a profile first.")


@router.post(
    "/current", response_model=ProfileDisplay, status_code=status.HTTP_201_CREATED
)
async def create_or_update_profile(
    response: Response,
    profile_data: ProfileUpdate,
    current_user: current_user_dependency,
    db: db_dependency,
) -> Any:
    """
    Create or update current user's profile.
    """
    profile, created = await profile_service.create_or_update_profile(
        db, current_user.id, profile_data
    )
    if not created:
        response.status_code = status.HTTP_200_OK

    return profile


# Profile Photos
@router.post("/current/photo", response_model=ProfilePhotoDisplay)
async def upload_profile_photo(
    db: db_dependency,
    current_user: current_user_dependency,
    file: UploadFile = File(...),
) -> Any:
    """
    Upload or replace a profile photo.
    """
    return await profile_service.add_profile_photo(db, current_user.id, file)


@router.get("/current/photo", response_model=ProfilePhotoDisplay)
async def get_profile_photo(
    current_user: current_user_dependency,
    db: db_dependency,
) -> Any:
    """
    Get current user's profile photo.
    """
    return await profile_service.get_profile_photo(db, current_user.id)


@router.delete("/current/photo", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_photo(
    current_user: current_user_dependency,
    db: db_dependency,
) -> None:
    """
    Delete current user's profile photo.
    """
    await profile_service.delete_profile_photo(db, current_user.id)
    return None
