from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from src.data import UserStatus


# Base schemas
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr


# Create schemas
class PermissionCreate(PermissionBase):
    pass


class RoleCreate(RoleBase):
    permissions: Optional[List[UUID]] = None


class UserCreate(UserBase):
    password: str
    roles: Optional[List[UUID]] = None


# Update schemas
class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[UUID]] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_verified: Optional[bool] = None
    status: Optional[UserStatus] = None
    roles: Optional[List[UUID]] = None


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


class UserDisplay(UserBase):
    id: UUID
    is_verified: bool
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


# Authentication schemas
class UserWithPassword(UserDisplay):
    password_hash: str

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime: lambda dt: dt.isoformat()}
    )


# Resolve forward references
RoleDisplay.model_rebuild()
UserDisplay.model_rebuild()
