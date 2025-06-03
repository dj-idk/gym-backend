import re
from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})


class TokenPayload(BaseModel):
    sub: UUID
    exp: datetime
    jti: str
    iat: datetime = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength requirements.

        Args:
            v: The password string to validate

        Returns:
            The validated password

        Raises:
            ValueError: If password doesn't meet security requirements
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class EmailVerification(BaseModel):
    token: str
