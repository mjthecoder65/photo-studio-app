from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.mixins import TimeStampMixin


class PhotoStatus(str, Enum):
    """Photo processing status."""

    UPLOADING = "uploading"
    PROCESSED = "processed"
    FAILED = "failed"


class Photo(Base):
    """Photo database model."""

    __tablename__ = "photos"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[PhotoStatus] = mapped_column(
        SQLEnum(PhotoStatus, native_enum=False, length=20),
        nullable=False,
        default=PhotoStatus.UPLOADING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Album(Base, TimeStampMixin):
    """Album database model."""

    __tablename__ = "albums"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AlbumPhoto(Base):
    """Association table for Album-Photo many-to-many relationship."""

    __tablename__ = "album_photos"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, nullable=False)
    album_id: Mapped[UUID] = mapped_column(
        ForeignKey("albums.id", ondelete="CASCADE"), nullable=False, index=True
    )
    photo_id: Mapped[UUID] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    album: Mapped["Album"] = relationship("Album", back_populates="photos")
    photo: Mapped["Photo"] = relationship("Photo", back_populates="albums")


# Pydantic models for API requests/responses


class PhotoResponse(BaseModel):
    """Photo response model."""

    id: UUID
    user_id: int
    storage_path: str
    status: PhotoStatus
    created_at: datetime

    class Config:
        from_attributes = True


class PhotoCreateRequest(BaseModel):
    """Photo creation request model."""

    storage_path: str = Field(min_length=1, description="Storage path for the photo")
    status: PhotoStatus = Field(
        default=PhotoStatus.UPLOADING, description="Initial status of the photo"
    )


class PhotoUpdateRequest(BaseModel):
    """Photo update request model."""

    storage_path: Optional[str] = Field(
        None, min_length=1, description="New storage path"
    )
    status: Optional[PhotoStatus] = Field(None, description="New status")


class AlbumResponse(BaseModel):
    """Album response model."""

    id: UUID
    user_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlbumCreateRequest(BaseModel):
    """Album creation request model."""

    name: str = Field(min_length=1, max_length=255, description="Album name")
    description: Optional[str] = Field(None, description="Album description")


class AlbumUpdateRequest(BaseModel):
    """Album update request model."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="New album name"
    )
    description: Optional[str] = Field(None, description="New album description")
