from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from uuid import UUID, uuid4
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from passlib.context import CryptContext

from src.data import User, Role
from src.schema import TokenPayload, UserCreate, UserUpdate
from src.service.base import BaseCRUDService
from src.utils.exceptions import BadRequest, Unauthorized, ServiceUnavailable, NotFound
from src.utils.redis import (
    redis_client,
    store_token_in_redis,
    revoke_token_in_redis,
    check_token_in_redis,
)
from src.utils import logger
from src.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService(BaseCRUDService[User, UserCreate, UserUpdate]):
    """A service for user authentication."""

    def __init__(self):
        super().__init__(User)
        self.ALGORITHM = "HS256"
        self.PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 24

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    def create_access_token(
        self, subject: Union[str, UUID], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        token_id = str(uuid4())

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "jti": token_id,
            "iat": datetime.now(timezone.utc),
        }

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=self.ALGORITHM
        )

        store_token_in_redis(token_id=token_id, user_id=str(subject), expires_at=expire)

        return encoded_jwt

    def create_otp() -> str:
        """Generate one-time password."""
        return "".join(str(random.randint(0, 9)) for _ in range(6))

    @staticmethod
    def calculate_token_expire_delta(now: datetime) -> datetime:
        """Calculate the expiration time for the access token."""
        return now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    async def request_phone_verification(
        self, db: AsyncSession, phone_number: str
    ) -> Dict[str, Any]:
        """Send a verification code to the user's phone number."""
        user = await self.get_by(db, phone_number=phone_number)

        if not user:
            raise NotFound("User with this phone number not found")
        if user.is_verified:
            raise BadRequest("User is already verified")

        verification_code = AuthService.create_otp()

        key = f"phone_verification:{phone_number}"

        redis_client.set(
            key,
            verification_code,
            ex=600,
        )

        # TODO: In a real application, send the code via SMS using a service
        # For now, we'll just return the code for testing purposes

        return {
            "message": "Verification code sent to your phone number",
            "code": verification_code,
        }

    async def confirm_phone_verification(
        self, db: AsyncSession, phone_number: str, code: str
    ) -> Dict[str, Any]:
        """Verify the code entered by the user."""
        user = await self.get_by(db, phone_number=phone_number)

        if not user:
            raise NotFound("User with this phone number not found")
        if user.is_verified:
            raise BadRequest("User is already verified")

        key = f"phone_verification:{phone_number}"

        stored_code = redis_client.get(key)

        if not stored_code:
            raise NotFound("Verification code expired or not found")

        if stored_code != code:
            raise BadRequest("Invalid verification code")

        user.is_verified = True
        db.add(user)
        await db.commit()
        await db.refresh(user)

        redis_client.delete(key)

        access_token = self.create_access_token(user.id)

        return {
            "message": "Phone number verified successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": AuthService.calculate_token_expire_delta(datetime.now()),
        }

    async def register_user(
        self, db: AsyncSession, user_data: UserCreate
    ) -> Dict[str, Any]:
        """Register a new user and return access token."""
        try:
            existing_user = await self.get_by(db, phone_number=user_data.phone_number)
            if existing_user:
                raise BadRequest("Phone number already registered")

            hashed_password = self.get_password_hash(user_data.password)

            result = await db.execute(select(Role).filter(Role.name == "member"))
            member_role = result.scalars().first()

            if not member_role:
                raise ServiceUnavailable("Role system not initialized")

            user_in_db = User(
                phone_number=user_data.phone_number,
                hashed_password=hashed_password,
                is_active=True,
                is_verified=False,
                roles=[member_role],
            )

            db.add(user_in_db)

            verification_code = AuthService.create_otp()
            key = f"phone_verification:{user_data.phone_number}"

            redis_client.set(
                key,
                verification_code,
                ex=600,
            )

            await db.commit()
            await db.refresh(user_in_db)

            # TODO: In a real application, send the code via SMS

            return {
                "message": "User registered. Verification code sent to your phone number",
                "code": verification_code,
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to register user: {str(e)}")
            raise ServiceUnavailable("Failed to register user")

    async def authenticate_user(
        self, db: AsyncSession, credential: str, password: str
    ) -> Dict[str, Any]:
        """Authenticate user and return access token."""
        user = (
            await self.get_by(db, email=credential)
            or await self.get_by(db, username=credential)
            or await self.get_by(db, phone_number=credential)
        )

        if not user:
            raise Unauthorized("Invalid credentials")
        if not user.is_verified:
            raise Unauthorized(
                "User is not verified. Please verify your phone number first."
            )
        if not user.is_active:
            raise Unauthorized("User account is disabled")
        if not self.verify_password(password, user.hashed_password):
            raise Unauthorized("Invalid credentials")

        access_token = self.create_access_token(user.id)

        user.last_login = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": AuthService.calculate_token_expire_delta(datetime.now()),
        }

    async def refresh_token(self, db: AsyncSession, token: str) -> Dict[str, Any]:
        """Refresh access token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            token_data = TokenPayload(**payload)

            token_info = check_token_in_redis(token_data.jti)
            if not token_info or token_info.get("is_revoked", False):
                raise Unauthorized("Token has been invalidated")

            user = await self.get(db, token_data.sub)
            if not user:
                raise Unauthorized("Invalid token")

            if not user.is_active:
                raise Unauthorized("User account is disabled")

            access_token = self.create_access_token(user.id)

            revoke_token_in_redis(token_data.jti)

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_at": AuthService.calculate_token_expire_delta(datetime.now()),
            }
        except JWTError:
            raise Unauthorized("Invalid or expired token")

    async def logout(self, token: str) -> Dict[str, str]:
        """Invalidate the current token by revoking it in Redis."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            token_data = TokenPayload(**payload)

            if not revoke_token_in_redis(token_data.jti):
                raise ServiceUnavailable("Failed to revoke token")

            return {"message": "Successfully logged out"}
        except JWTError:
            raise Unauthorized("Invalid token")

    async def request_password_reset(
        self, db: AsyncSession, phone_number: str
    ) -> Dict[str, str]:
        """Generate password reset code and send it to user's phone number."""
        user = await self.get_by(db, phone_number=phone_number)
        if not user:
            return {
                "message": "Password reset code sent to your phone number",
            }
        reset_code = AuthService.create_otp()

        key = f"password_reset:{phone_number}"
        redis_client.set(
            key,
            reset_code,
            ex=3600,
        )

        # TODO: In a real application, send the code via SMS
        # For now, we'll just return the code for testing purposes

        return {
            "message": "Password reset code sent to your phone number",
            "code": reset_code,
        }

    async def reset_password(
        self, db: AsyncSession, phone_number: str, code: str, new_password: str
    ) -> Dict[str, str]:
        """Reset user password using verification code."""
        user = await self.get_by(db, phone_number=phone_number)
        if not user:
            raise NotFound("User with this phone number not found")

        key = f"password_reset:{phone_number}"
        stored_code = redis_client.get(key)

        if not stored_code:
            raise NotFound("Reset code expired or not found")

        if stored_code != code:
            raise BadRequest("Invalid reset code")

        hashed_password = self.get_password_hash(new_password)
        user.hashed_password = hashed_password
        db.add(user)
        await db.commit()

        redis_client.delete(key)

        return {"message": "Password has been reset successfully"}


auth_service = AuthService()
