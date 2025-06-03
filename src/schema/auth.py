import re
from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


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


class PhoneVerificationRequest(BaseModel):
    """Schema for requesting phone verification."""

    phone_number: str = Field(
        ..., description="Phone number to verify", example="09123456789"
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """
        Validate that the phone number starts with 09 and has 11 digits total.

        Args:
            v: The phone number string to validate

        Returns:
            The validated phone number

        Raises:
            ValueError: If phone number doesn't match the required format
        """
        pattern = r"^09\d{9}$"
        if not re.match(pattern, v):
            raise ValueError("Phone number must start with 09 and have 11 digits total")
        return v


class PhoneVerificationConfirm(BaseModel):
    """Schema for confirming phone verification."""

    phone_number: str = Field(
        ..., description="Phone number to verify", example="09123456789"
    )
    code: str = Field(..., description="Verification code", example="123456")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """
        Validate that the phone number starts with 09 and has 11 digits total.

        Args:
            v: The phone number string to validate

        Returns:
            The validated phone number

        Raises:
            ValueError: If phone number doesn't match the required format
        """
        pattern = r"^09\d{9}$"
        if not re.match(pattern, v):
            raise ValueError("Phone number must start with 09 and have 11 digits total")
        return v
