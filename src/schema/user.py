from datetime import datetime
from typing import List, Optional
from uuid import UUID
import re

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from src.data import UserStatus
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
