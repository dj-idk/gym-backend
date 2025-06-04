from datetime import datetime
from typing import List, Optional
from uuid import UUID
import re

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from .validators import validate_password, validate_phone_number


# Base schemas
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


# Create schemas
class PermissionCreate(PermissionBase):
    pass


class RoleCreate(RoleBase):
    permissions: Optional[List[UUID]] = None


class UserCreate(BaseModel):
    phone_number: str
    password: str

    _validate_phone = field_validator("phone_number")(validate_phone_number)
    _validate_password = field_validator("password", mode="after")(validate_password)


# Update schemas
class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[UUID]] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


# Display schemas
class PermissionDisplay(PermissionBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()},
    )


class RoleDisplay(RoleBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List["PermissionDisplay"] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()},
    )


class UserDisplay(BaseModel):
    id: UUID
    phone_number: str
    username: Optional[str]
    email: Optional[EmailStr]
    is_verified: bool
    is_email_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: List["RoleSummary"] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()}
    )


# Summary schemas (for pagination responses)
class PermissionSummary(PermissionBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class RoleSummary(RoleBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    id: UUID
    email: EmailStr
    is_verified: bool
    is_email_verified: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()}
    )


class UserUpdateResponse(BaseModel):
    user: UserDisplay
    messages: dict


class EmailVerificationResponse(BaseModel):
    """Response model for email verification"""

    success: bool
    message: str
    user_id: Optional[UUID] = None

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()}
    )


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., description="New password to set")

    _validate_password_fields = field_validator(
        "current_password", "new_password", mode="after"
    )(validate_password)

    @field_validator("new_password")
    def passwords_must_be_different(cls, v, info):
        if "current_password" in info.data and v == info.data["current_password"]:
            raise ValueError("New password must be different from current password")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "Current$3cureP@ss",
                "new_password": "New$3cureP@ss123",
            }
        }
    )


class PasswordChangeResponse(BaseModel):
    success: bool
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "message": "Password changed successfully"}
        }
    )


# Resolve forward references
RoleDisplay.model_rebuild()
UserDisplay.model_rebuild()
