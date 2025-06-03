from enum import Enum
from typing import Generic, List, TypeVar, Dict, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class OrderDirection(str, Enum):
    """Order direction enum. Used for sorting in API responses."""

    ASC = "asc"
    DESC = "desc"


class BulkID(BaseModel):
    """Schema for batch deleting media"""

    ids: List[int]


class Pagination(BaseModel):
    """
    Schema for pagination information.
    Used for API responses that return paginated data.
    """

    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Number of items per page")
    skip: int = Field(..., description="Number of items skipped")
    current_page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    has_next: bool = Field(..., description="Whether there is a next page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response.
    """

    items: List[T]
    pagination: Pagination

    model_config = ConfigDict(from_attributes=True)


class MediaEntityBase(BaseModel):
    file_path: str
    file_url: str
    file_name: str
    file_size: float
    file_type: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    media_metadata: Optional[Dict] = None


class MediaEntityDisplay(MediaEntityBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()},
    )
