from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date
from uuid import UUID

from src.data import Gender
from .common import MediaEntityDisplay


class ProfileBase(BaseModel):
    first_name: str = Field(None, max_length=50)
    last_name: str = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    bio: Optional[str] = None
    height: Optional[float] = Field(None, gt=10, lt=400)
    weight: Optional[float] = Field(None, gt=0, lt=300)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10, pattern=r"^[1-9][0-9]{9}$")


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    bio: Optional[str] = None
    height: Optional[float] = Field(None, gt=10, lt=400)
    weight: Optional[float] = Field(None, gt=0, lt=300)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10, pattern=r"^[1-9][0-9]{9}$")


class ProfilePhotoDisplay(MediaEntityDisplay):
    profile_id: UUID

    model_config = ConfigDict(from_attributes=True)


class ProfilePhotoSummaryDisplay(BaseModel):

    file_url: str
    alt_text: str

    model_config = ConfigDict(from_attributes=True)


class ProfileDisplay(ProfileBase):
    id: UUID
    user_id: UUID
    photo: Optional[ProfilePhotoSummaryDisplay]

    model_config = ConfigDict(from_attributes=True)
