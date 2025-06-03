import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, String, Float, JSON, Text
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID

from src.data.database import Base


class BaseEntity(Base):
    """Base class for all database models with common fields"""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class MediaEntity(BaseEntity):
    """Base class for media entities"""

    __abstract__ = True

    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Float, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)

    alt_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
