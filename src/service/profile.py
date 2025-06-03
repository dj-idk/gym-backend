from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union, List
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from sqlalchemy.sql.expression import Select

from src.data import User, Profile, ProfilePhoto, ProgressRecord, ProgressPhoto
from src.schema import (
    ProfileCreate,
    ProfileUpdate,
    ProfileDisplay,
    ProgressRecordCreate,
    ProgressRecordUpdate,
)
from src.service.base import BaseCRUDService
from src.utils.exceptions import BadRequest, Unauthorized, ServiceUnavailable, NotFound
from src.utils import logger
from src.utils.storage import upload_image, delete_file
from src.config import settings


class ProfileService(BaseCRUDService[Profile, ProfileCreate, ProfileUpdate]):
    """A service for managing user profiles."""

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

    async def create_profile(
        self, db: AsyncSession, user_id: UUID, profile_data: ProfileCreate
    ) -> Profile:
        """
        Create a new profile for a user.

        Args:
            db: Database session
            user_id: ID of the user
            profile_data: Profile creation data

        Returns:
            The created profile
        """
        # Check if user exists
        user_query = select(User).where(User.id == user_id)
        result = await db.execute(user_query)
        user = result.scalars().first()

        if not user:
            raise NotFound(f"User with ID {user_id} not found")

        # Check if profile already exists
        existing_profile = await self.get_profile_by_user_id(db, user_id)
        if existing_profile:
            raise BadRequest(f"Profile for user with ID {user_id} already exists")

        # Create profile object with user_id
        profile_dict = profile_data.model_dump()
        profile = Profile(user_id=user_id, **profile_dict)

        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        return profile

    async def update_profile(
        self, db: AsyncSession, user_id: UUID, profile_update: ProfileUpdate
    ) -> Profile:
        """
        Update a user's profile.

        Args:
            db: Database session
            user_id: ID of the user
            profile_update: Profile update data

        Returns:
            The updated profile
        """
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        updated_profile = await self.update(db, db_obj=profile, obj_in=profile_update)
        return updated_profile

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
                is_primary=True,  # Always true since there's only one photo
            )

            db.add(photo)
            await db.commit()
            await db.refresh(photo)

            return photo

        except Exception as e:
            logger.error(f"Error uploading profile photo: {str(e)}")
            raise ServiceUnavailable("Failed to upload profile photo")

    async def delete_profile_photo(
        self, db: AsyncSession, user_id: UUID, photo_id: UUID
    ) -> None:
        """
        Delete a profile photo.

        Args:
            db: Database session
            user_id: ID of the user
            photo_id: ID of the photo to delete
        """
        # Get the profile for this user
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        # Get the photo
        query = select(ProfilePhoto).where(
            ProfilePhoto.id == photo_id, ProfilePhoto.profile_id == profile.id
        )
        result = await db.execute(query)
        photo = result.scalars().first()

        if not photo:
            raise NotFound(f"Photo with ID {photo_id} not found")

        # Delete the file from storage
        try:
            if photo.file_path:
                delete_file(photo.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete photo file: {str(e)}")

        # Delete the database record
        await db.delete(photo)
        await db.commit()

    # Progress Record Methods
    async def create_progress_record(
        self, db: AsyncSession, user_id: UUID, record_data: ProgressRecordCreate
    ) -> ProgressRecord:
        """
        Create a new progress record for a user.

        Args:
            db: Database session
            user_id: ID of the user
            record_data: Progress record creation data

        Returns:
            The created progress record
        """
        # Check if profile exists
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        # Create progress record
        record_dict = record_data.model_dump()
        record = ProgressRecord(profile_id=profile.id, **record_dict)

        db.add(record)
        await db.commit()
        await db.refresh(record)

        return record

    async def get_progress_records(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        start_date: str = None,
        end_date: str = None,
    ) -> List[ProgressRecord]:
        """
        Get progress records for a user with optional date filtering.

        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            start_date: Optional start date for filtering (ISO format)
            end_date: Optional end date for filtering (ISO format)

        Returns:
            List of progress records
        """
        # Check if profile exists
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        # Build query
        query = select(ProgressRecord).where(ProgressRecord.profile_id == profile.id)

        # Apply date filters if provided
        if start_date:
            query = query.where(ProgressRecord.date >= start_date)
        if end_date:
            query = query.where(ProgressRecord.date <= end_date)

        # Apply ordering and pagination
        query = query.order_by(ProgressRecord.date.desc())
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        return result.scalars().all()

    async def get_progress_record(
        self, db: AsyncSession, user_id: UUID, record_id: UUID
    ) -> ProgressRecord:
        """
        Get a specific progress record.

        Args:
            db: Database session
            user_id: ID of the user
            record_id: ID of the record

        Returns:
            The progress record
        """
        # Check if profile exists
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        # Get the record
        query = select(ProgressRecord).where(
            ProgressRecord.id == record_id, ProgressRecord.profile_id == profile.id
        )
        result = await db.execute(query)
        record = result.scalars().first()

        if not record:
            raise NotFound(f"Progress record with ID {record_id} not found")

        return record

    async def update_progress_record(
        self,
        db: AsyncSession,
        user_id: UUID,
        record_id: UUID,
        record_update: ProgressRecordUpdate,
    ) -> ProgressRecord:
        """
        Update a progress record.

        Args:
            db: Database session
            user_id: ID of the user
            record_id: ID of the record
            record_update: Update data

        Returns:
            The updated progress record
        """
        # Get the record
        record = await self.get_progress_record(db, user_id, record_id)

        # Update the record
        update_data = record_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)

        db.add(record)
        await db.commit()
        await db.refresh(record)

        return record

    async def delete_progress_record(
        self, db: AsyncSession, user_id: UUID, record_id: UUID
    ) -> None:
        """
        Delete a progress record.

        Args:
            db: Database session
            user_id: ID of the user
            record_id: ID of the record
        """
        # Get the record
        record = await self.get_progress_record(db, user_id, record_id)

        # Delete the record
        await db.delete(record)
        await db.commit()

    async def add_progress_photo(
        self,
        db: AsyncSession,
        user_id: UUID,
        file: UploadFile,
        category: str = None,
        notes: str = None,
    ) -> ProgressPhoto:
        """
        Add a progress photo.

        Args:
            db: Database session
            user_id: ID of the user
            file: Uploaded file
            category: Optional category for the photo
            notes: Optional notes for the photo

        Returns:
            The created progress photo
        """
        # Check if profile exists
        profile = await self.get_profile_by_user_id(db, user_id)
        if not profile:
            raise NotFound(f"Profile for user with ID {user_id} not found")

        # Process and save the file
        try:
            # Upload the image to storage
            public_url, object_key = await upload_image(
                upload_file=file, entity_type="progress", entity_name=f"user_{user_id}"
            )

            # Create photo record
            photo = ProgressPhoto(
                profile_id=profile.id,
                file_path=object_key,
                file_url=public_url,
                file_name=file.filename,
                file_size=file.size,
                file_type=file.content_type,
                category=category,
                notes=notes,
                date=datetime.now(),
            )

            db.add(photo)
            await db.commit()
            await db.refresh(photo)

            return photo

        except Exception as e:
            logger.error(f"Error uploading progress photo: {str(e)}")
            raise ServiceUnavailable("Failed to upload progress photo")


# Create an instance of the service
profile_service = ProfileService(Profile)
