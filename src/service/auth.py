from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from passlib.context import CryptContext

from src.data import User
from src.schema import TokenPayload, UserCreate, UserUpdate
from src.service.base import BaseCRUDService
from src.utils.exceptions import BadRequest, Unauthorized, ServiceUnavailable
from src.utils.redis import (
    store_token_in_redis,
    revoke_token_in_redis,
    check_token_in_redis,
)
from src.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService(BaseCRUDService[User, UserCreate, UserUpdate]):
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

    @staticmethod
    def calculate_expire_delta(now: datetime) -> datetime:
        """Calculate the expiration time for the access token."""
        return now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    async def register_user(
        self, db: AsyncSession, user_data: UserCreate
    ) -> Dict[str, Any]:
        """Register a new user and return access token."""
        existing_user = await self.get_by(db, email=user_data.email)
        if existing_user:
            raise BadRequest("Email already registered")

        hashed_password = self.get_password_hash(user_data.password)
        user_in_db = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
        )

        db.add(user_in_db)
        await db.commit()
        await db.refresh(user_in_db)

        access_token = self.create_access_token(user_in_db.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": AuthService.calculate_expire_delta(datetime.now()),
        }

    async def authenticate_user(
        self, db: AsyncSession, username_or_email: str, password: str
    ) -> Dict[str, Any]:
        """Authenticate user and return access token."""
        user = await self.get_by(db, email=username_or_email) or await self.get_by(
            db, username=username_or_email
        )
        if not user:
            raise Unauthorized("Invalid credentials")

        if not self.verify_password(password, user.hashed_password):
            raise Unauthorized("Invalid credentials")

        if not user.is_active:
            raise Unauthorized("User account is disabled")

        access_token = self.create_access_token(user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": AuthService.calculate_expire_delta(datetime.now()),
        }

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
        self, db: AsyncSession, email: str
    ) -> Dict[str, str]:
        """Generate password reset token and send it to user's email."""
        user = await self.get_by(db, email=email)
        if not user:
            # Don't reveal that the user doesn't exist
            return {
                "message": "If the email exists, a password reset link has been sent"
            }

        # Generate reset token
        reset_token = self.create_access_token(
            user.id,
            expires_delta=timedelta(hours=self.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
        )

        # TODO: Send email with reset token
        # This would typically involve an email service integration

        return {"message": "If the email exists, a password reset link has been sent"}

    async def reset_password(
        self, db: AsyncSession, token: str, new_password: str
    ) -> Dict[str, str]:
        """Reset user password using token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            token_data = TokenPayload(**payload)

            # Check if token is valid in Redis
            token_info = check_token_in_redis(token_data.jti)
            if not token_info or token_info.get("is_revoked", False):
                raise Unauthorized("Token has been invalidated")

            user = await self.get(db, token_data.sub)
            if not user:
                raise Unauthorized("Invalid token")

            # Update password
            hashed_password = self.get_password_hash(new_password)
            user.hashed_password = hashed_password
            db.add(user)
            await db.commit()

            # Revoke the used token
            revoke_token_in_redis(token_data.jti)

            return {"message": "Password has been reset successfully"}
        except JWTError:
            raise Unauthorized("Invalid or expired token")

    async def verify_email(self, db: AsyncSession, token: str) -> Dict[str, str]:
        """Verify user email with token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            token_data = TokenPayload(**payload)

            # Check if token is valid in Redis
            token_info = check_token_in_redis(token_data.jti)
            if not token_info or token_info.get("is_revoked", False):
                raise Unauthorized("Token has been invalidated")

            user = await self.get(db, token_data.sub)
            if not user:
                raise Unauthorized("Invalid token")

            # Mark email as verified
            user.is_verified = True
            db.add(user)
            await db.commit()

            # Revoke the used token
            revoke_token_in_redis(token_data.jti)

            return {"message": "Email verified successfully"}
        except JWTError:
            raise Unauthorized("Invalid or expired token")

    async def refresh_token(self, db: AsyncSession, token: str) -> Dict[str, Any]:
        """Refresh access token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            token_data = TokenPayload(**payload)

            # Check if token is valid in Redis
            token_info = check_token_in_redis(token_data.jti)
            if not token_info or token_info.get("is_revoked", False):
                raise Unauthorized("Token has been invalidated")

            user = await self.get(db, token_data.sub)
            if not user:
                raise Unauthorized("Invalid token")

            if not user.is_active:
                raise Unauthorized("User account is disabled")

            # Create new access token
            access_token = self.create_access_token(user.id)

            # Revoke the old token
            revoke_token_in_redis(token_data.jti)

            return {"access_token": access_token, "token_type": "bearer"}
        except JWTError:
            raise Unauthorized("Invalid or expired token")


auth_service = AuthService()
