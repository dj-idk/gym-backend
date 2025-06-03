import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Table,
    Column,
)
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseEntity


# Association table for many-to-many relationship between users and roles
user_role = Table(
    "user_role",
    BaseEntity.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
)

# Association table for many-to-many relationship between roles and permissions
role_permission = Table(
    "role_permission",
    BaseEntity.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id"),
        primary_key=True,
    ),
)


class UserStatus(str, enum.Enum):
    """Enum for user status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class Role(BaseEntity):
    """Role model for authorization"""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        secondary=user_role, back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        secondary=role_permission, back_populates="roles"
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Permission(BaseEntity):
    """Permission model for fine-grained access control"""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=role_permission, back_populates="permissions"
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class User(BaseEntity):
    """User model for authentication"""

    __tablename__ = "users"
    phone_number: Mapped[Optional[str]] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.PENDING_VERIFICATION, nullable=False
    )

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=user_role, back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
