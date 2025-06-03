from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from src.data import User, Profile, ProfilePhoto
from src.schema import ProfileUpdate

from src.service.base import BaseCRUDService
from src.utils.exceptions import ServiceUnavailable, NotFound
from src.utils import logger
from src.utils.storage import upload_image, delete_file
from src.config import settings


class ProfileService(BaseCRUDService[Profile, ProfileUpdate, ProfileUpdate]):
    """A service for managing user profiles."""

    def __init__(self):
        super().__init__(Profile)

    async def get_profile_by_user_id(
        self, db: AsyncSession, user_id: UUID
    ) -> Optional[Profile]:
        """
        Get a profile by user ID.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            The profile if found, None otherwise
        """
        return await self.get_by(db, user_id=user_id)

    async def create_or_update_profile(
        self, db: AsyncSession, user_id: UUID, profile_data: ProfileUpdate
    ) -> tuple[Profile, bool]:
        """
        Create a new profile for a user or update existing one.

        Args:
            db: Database session
            user_id: ID of the user
            profile_data: Profile data for creation or update

        Returns:
            Tuple containing (profile, created) where created is a boolean
            indicating if a new profile was created (True) or updated (False)
        """
        user = await db.get(User, user_id)
        if not user:
            raise NotFound(f"User with ID {user_id} not found")

        # Check if profile already exists
        existing_profile = await self.get_profile_by_user_id(db, user_id)

        if existing_profile:
            # Update existing profile
            updated_profile = await self.update(
                db, db_obj=existing_profile, obj_in=profile_data
            )
            return updated_profile, False
        else:
            # Create new profile
            profile_dict = profile_data.model_dump()
            profile = Profile(user_id=user_id, **profile_dict)

            db.add(profile)
            await db.commit()
            await db.refresh(profile)

            return profile, True

    async def add_profile_photo(
        self, db: AsyncSession, user_id: UUID, file: UploadFile, is_primary: bool = True
    ) -> ProfilePhoto:
        """
        Add or replace a profile photo.
        Since there's only one profile photo per user, this will replace any existing photo.

        Args:
            db: Database session
            user_id: ID of the user
            file: Uploaded file
            is_primary: Whether this is the primary profile photo (always True for single photo)

        Returns:
            The created profile photo
        """
        # Check if profile exists
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        # Check if a photo already exists and delete it
        existing_photo_query = select(ProfilePhoto).where(
            ProfilePhoto.profile_id == profile.id
        )
        result = await db.execute(existing_photo_query)
        existing_photo = result.scalars().first()

        if existing_photo:
            # Delete the existing photo file from storage
            try:
                if existing_photo.file_path:
                    delete_file(existing_photo.file_path)
            except Exception as e:
                logger.warning(f"Failed to delete existing photo file: {str(e)}")

            # Delete the existing photo record
            await db.delete(existing_photo)
            await db.commit()

        # Process and save the new file
        try:
            # Upload the image to storage
            public_url, object_key = await upload_image(
                upload_file=file, entity_type="profile", entity_name=f"user_{user_id}"
            )

            # Create photo record
            photo = ProfilePhoto(
                profile_id=profile.id,
                file_path=object_key,
                file_url=public_url,
                file_name=file.filename,
                file_size=file.size,
                file_type=file.content_type,
                alt_text=f"User {profile.first_name if profile.first_name else str(user_id)} profile photo",
            )

            db.add(photo)
            await db.commit()
            await db.refresh(photo)

            return photo

        except Exception as e:
            logger.error(f"Error uploading profile photo: {str(e)}")
            raise ServiceUnavailable("Failed to upload profile photo")

    async def get_profile_photo(
        self, db: AsyncSession, user_id: UUID
    ) -> Optional[ProfilePhoto]:
        """
        Get a user's profile photo.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            The profile photo if found, None otherwise
        """
        # Get the profile for this user
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        # Get the photo (there should be only one)
        query = select(ProfilePhoto).where(ProfilePhoto.profile_id == profile.id)
        result = await db.execute(query)
        photo = result.scalars().first()

        if not photo:
            raise NotFound("Profile photo not found")

        return photo

    async def delete_profile_photo(self, db: AsyncSession, user_id: UUID) -> None:
        """
        Delete a user's profile photo.
        Since there's only one profile photo per user, no photo ID is needed.

        Args:
            db: Database session
            user_id: ID of the user
        """
        # Get the profile for this user
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        # Get the photo (there should be only one)
        query = select(ProfilePhoto).where(ProfilePhoto.profile_id == profile.id)
        result = await db.execute(query)
        photo = result.scalars().first()

        if not photo:
            # No photo to delete
            return None

        # Delete the file from storage
        try:
            if photo.file_path:
                delete_file(photo.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete photo file: {str(e)}")

        # Delete the database record
        await db.delete(photo)
        await db.commit()


profile_service = ProfileService()
