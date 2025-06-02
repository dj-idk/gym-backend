from enum import Enum
from typing import List

from pydantic import BaseModel, Field


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


class OrderDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class BulkID(BaseModel):
    """Schema for batch deleting media"""

    ids: List[int]
