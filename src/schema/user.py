from datetime import datetime
from typing import List, Optional
from uuid import UUID
import re

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from src.data import UserStatus


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

    @field_validator("password", mode="after")
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


# Update schemas
class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[UUID]] = None


class UserUpdate(BaseModel):
    pass


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
    status: UserStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: List["RoleDisplay"] = Field(default_factory=list)

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
    status: UserStatus
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()}
    )


# Resolve forward references
RoleDisplay.model_rebuild()
UserDisplay.model_rebuild()
