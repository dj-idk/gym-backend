import re
from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from .validators import validate_phone_number, validate_password


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
    phone_number: str = Field(..., validate_default=True)

    _validate_phone = field_validator("phone_number")(validate_phone_number)


class PasswordReset(BaseModel):
    phone_number: str = Field(..., validate_default=True)
    code: str
    new_password: str = Field(..., validate_default=True)

    _validate_phone = field_validator("phone_number")(validate_phone_number)
    _validate_password = field_validator("new_password", mode="after")(
        validate_password
    )


class PhoneVerificationRequest(BaseModel):
    """Schema for requesting phone verification."""

    phone_number: str = Field(
        ...,
        description="Phone number to verify",
        example="09123456789",
        validate_default=True,
    )

    _validate_phone = field_validator("phone_number")(validate_phone_number)


class PhoneVerificationConfirm(BaseModel):
    """Schema for confirming phone verification."""

    phone_number: str = Field(
        ...,
        description="Phone number to verify",
        example="09123456789",
        validate_default=True,
    )
    code: str = Field(..., description="Verification code", example="123456")

    _validate_phone = field_validator("phone_number")(validate_phone_number)
