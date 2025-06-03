from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date
from uuid import UUID

from src.data import Gender


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
    postal_code: Optional[str] = Field(
        None, max_length=10, pattern=r"\b(?!(\d)\1{3})[13-9]{4}[1346-9][013-9]{5}\b"
    )


class ProfileCreate(ProfileBase):
    pass


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
    postal_code: Optional[str] = Field(
        None, max_length=10, pattern=r"\b(?!(\d)\1{3})[13-9]{4}[1346-9][013-9]{5}\b"
    )


class ProfileDisplay(ProfileBase):
    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)
