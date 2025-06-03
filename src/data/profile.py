from datetime import date
from typing import Optional
import enum

from sqlalchemy import String, Date, ForeignKey, Float, Text, Enum
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseEntity, MediaEntity
from .user import User


class Gender(str, enum.Enum):
    """User gender"""

    MALE = "male"
    FEMALE = "female"


class Profile(BaseEntity):
    """User profile information"""

    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(Enum(Gender), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="profile")
    photo: Mapped[list["ProfilePhoto"]] = relationship(
        "ProfilePhoto", back_populates="profile", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Profile {self.first_name} {self.last_name}>"


class ProfilePhoto(MediaEntity):
    """User profile photo"""

    __tablename__ = "profile_photos"

    profile_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False
    )

    # Relationship
    profile: Mapped["Profile"] = relationship("Profile", back_populates="photo")

    def __repr__(self) -> str:
        return f"<ProfilePhoto {self.file_name}>"
