import secrets
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.data import User
from src.schema.user import UserCreate, UserUpdate
from src.schema import PaginatedResponse
from src.service.base import BaseCRUDService
from src.config import settings


class UserService(BaseCRUDService[User, UserCreate, UserUpdate]):
    """
    Service for user-related operations.
    """

    async def get_user(self, db: AsyncSession, user_id: UUID) -> User:
        """
        Get a user by ID.
        """
        user = await self.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Get a user by email.
        """
        return await self.get_by(db, email=email)

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        Get a user by username.
        """
        return await self.get_by(db, username=username)

    async def update_username(
        self, db: AsyncSession, user_id: UUID, new_username: str
    ) -> Tuple[User, Dict[str, Any]]:
        """
        Update a user's username with conflict checking.

        Args:
            db: Database session
            user_id: User ID
            new_username: New username to set

        Returns:
            Tuple of (updated user, message dict)
        """
        user = await self.get_user(db, user_id)
        messages = {}

        # Skip if username is not changing
        if not new_username or new_username == user.username:
            messages["username"] = {"status": "unchanged"}
            return user, messages

        # Check if username is already taken by another user
        existing_user = await self.get_by_username(db, username=new_username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

        # Update username
        update_data = {"username": new_username}
        updated_user = await self.update(db, db_obj=user, obj_in=update_data)
        messages["username"] = {"status": "updated", "new_value": new_username}

        return updated_user, messages

    async def update_email(
        self, db: AsyncSession, user_id: UUID, new_email: str
    ) -> Tuple[User, Dict[str, Any]]:
        """
        Update a user's email with verification process.

        Args:
            db: Database session
            user_id: User ID
            new_email: New email to set

        Returns:
            Tuple of (user, message dict with verification info)
        """
        user = await self.get_user(db, user_id)
        messages = {}

        # Skip if email is not changing
        if not new_email or new_email == user.email:
            messages["email"] = {"status": "unchanged"}
            return user, messages

        # Check if email is already taken by another user
        existing_user = await self.get_by_email(db, email=new_email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        expiration = datetime.utcnow() + timedelta(hours=24)

        # Store pending email change
        update_data = {
            "pending_email": new_email,
            "email_verification_token": verification_token,
            "email_token_expires": expiration,
        }

        updated_user = await self.update(db, db_obj=user, obj_in=update_data)

        # Generate verification URL
        verification_url = f"{settings.SERVER_HOST}{settings.API_V1_STR}/users/verify-email?token={verification_token}"

        messages["email"] = {
            "status": "verification_required",
            "new_email": new_email,
            "verification_url": verification_url,
            "expires_at": expiration.isoformat(),
        }

        return updated_user, messages

    async def update_user(
        self, db: AsyncSession, user_id: UUID, user_update: UserUpdate
    ) -> Dict[str, Any]:
        """
        Update a user with separate handling for username, email, and other fields.

        Args:
            db: Database session
            user_id: User ID
            user_update: User update data

        Returns:
            Dict containing updated user and messages about the update process
        """
        user = await self.get_user(db, user_id)
        update_messages = {}

        # Handle username update
        if hasattr(user_update, "username") and user_update.username is not None:
            user, username_messages = await self.update_username(
                db, user_id, user_update.username
            )
            update_messages.update(username_messages)

        # Handle email update
        if hasattr(user_update, "email") and user_update.email is not None:
            user, email_messages = await self.update_email(
                db, user_id, user_update.email
            )
            update_messages.update(email_messages)

        return {"user": user, "messages": update_messages}

    async def verify_email(self, db: AsyncSession, token: str) -> User:
        """
        Verify a user's email address using the verification token.

        Args:
            db: Database session
            token: Email verification token

        Returns:
            Updated user object
        """
        # Find user with this token
        query = select(User).where(User.email_verification_token == token)
        result = await db.execute(query)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

        # Check if token is expired
        if user.email_token_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired",
            )

        # Update email and clear verification fields
        update_data = {
            "email": user.pending_email,
            "pending_email": None,
            "email_verification_token": None,
            "email_token_expires": None,
            "email_verified": True,
        }

        return await self.update(db, db_obj=user, obj_in=update_data)

    async def get_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> PaginatedResponse:
        """
        Get multiple users with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            PaginatedResponse with users
        """
        items, pagination = await self.get_multi(
            db, skip=skip, limit=limit, order_by="created_at"
        )

        return PaginatedResponse(items=items, pagination=pagination)

    async def search_users(
        self, db: AsyncSession, query: str, skip: int = 0, limit: int = 100
    ) -> PaginatedResponse:
        """
        Search users by name, email, or username.

        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            PaginatedResponse with matching users
        """
        search_filter = or_(
            User.email.ilike(f"%{query}%"),
            User.username.ilike(f"%{query}%"),
            User.profile.first_name.ilike(f"%{query}%"),
            User.profile.last_name.ilike(f"%{query}%"),
        )

        items, pagination = await self.get_multi_by_filter(
            db,
            query_filter=search_filter,
            skip=skip,
            limit=limit,
            order_by="created_at",
        )

        return PaginatedResponse(items=items, pagination=pagination)

    async def activate_user(self, db: AsyncSession, user_id: UUID) -> User:
        """
        Activate a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Updated user object
        """
        user = await self.get_user(db, user_id)
        return await self.update(db, db_obj=user, obj_in={"is_active": True})

    async def deactivate_user(self, db: AsyncSession, user_id: UUID) -> User:
        """
        Deactivate a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Updated user object
        """
        user = await self.get_user(db, user_id)
        return await self.update(db, db_obj=user, obj_in={"is_active": False})


# Create a singleton instance
user_service = UserService(User)
