import secrets
import json
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import pwd_context
from src.data import User
from src.utils.exceptions import NotFound, BadRequest
from src.utils.redis import redis_client
from src.schema.user import UserCreate, UserUpdate
from src.schema import PaginatedResponse
from src.service.base import BaseCRUDService
from src.config import settings


class UserService(BaseCRUDService[User, UserCreate, UserUpdate]):
    """
    Service for user management operations.
    """

    async def get_user(self, db: AsyncSession, user_id: UUID) -> User:
        """
        Get a user by ID.
        """
        user = await self.get(db, user_id)
        if not user:
            raise NotFound("User not found")
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

        if not new_username or new_username == user.username:
            messages["username"] = {"status": "unchanged"}
            return user, messages

        existing_user = await self.get_by_username(db, username=new_username)
        if existing_user and existing_user.id != user_id:
            raise BadRequest("Username already taken")

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

        if not new_email or new_email == user.email:
            messages["email"] = {"status": "unchanged"}
            return user, messages

        existing_user = await self.get_by_email(db, email=new_email)
        if existing_user and existing_user.id != user_id:
            raise BadRequest("Email already registered")

        verification_token = secrets.token_urlsafe(32)
        expiration_seconds = 24 * 60 * 60
        expiration = datetime.now(timezone.utc) + timedelta(hours=24)

        redis_key = f"email_verification:{verification_token}"
        redis_value = {
            "user_id": str(user_id),
            "new_email": new_email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        redis_client.setex(redis_key, expiration_seconds, json.dumps(redis_value))

        verification_url = f"{settings.SERVER_HOST}{settings.API_V1_STR}/users/verify-email?token={verification_token}"

        messages["email"] = {
            "status": "verification_required",
            "new_email": new_email,
            "verification_url": verification_url,
            "expires_at": expiration.isoformat(),
        }

        return user, messages

    async def verify_email(self, db: AsyncSession, token: str) -> User:
        """
        Verify a user's email address using the verification token.

        Args:
            db: Database session
            token: Email verification token

        Returns:
            Updated user object
        """
        redis_key = f"email_verification:{token}"
        token_data = redis_client.get(redis_key)

        if not token_data:
            raise BadRequest("Invalid verification token")

        try:
            token_info = json.loads(token_data)
            user_id = UUID(token_info["user_id"])
            new_email = token_info["new_email"]
        except (json.JSONDecodeError, KeyError, ValueError):
            raise BadRequest("Invalid token data")

        user = await self.get_user(db, user_id)

        update_data = {
            "email": new_email,
            "is_email_verified": True,
        }

        redis_client.delete(redis_key)

        await self.update(db, db_obj=user, obj_in=update_data)

        return {
            "success": True,
            "message": "Email verified successfully",
            "user_id": user.id,
        }

    async def change_password(
        self, db: AsyncSession, user_id: UUID, current_password: str, new_password: str
    ) -> Dict[str, Any]:
        """
        Change a user's password with verification of current password.

        Args:
            db: Database session
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            Dict with success message and status
        """
        user = await self.get_user(db, user_id)

        # Verify current password
        if not pwd_context.verify(current_password, user.hashed_password):
            raise BadRequest("Current password is incorrect")

        update_data = {"hashed_password": pwd_context.hash(new_password)}
        await self.update(db, db_obj=user, obj_in=update_data)

        return {
            "success": True,
            "message": "Password changed successfully",
        }

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


user_service = UserService(User)
