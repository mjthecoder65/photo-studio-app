from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.photo import Photo, PhotoStatus


class PhotoRepository:
    """Repository for Photo database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        storage_path: str,
        status: PhotoStatus = PhotoStatus.UPLOADING,
    ) -> Photo:
        photo = Photo(user_id=user_id, storage_path=storage_path, status=status)
        self.db.add(photo)
        await self.db.commit()
        await self.db.refresh(photo)
        return photo

    async def get_by_id(self, photo_id: UUID) -> Optional[Photo]:
        stmt = select(Photo).where(Photo.id == photo_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Photo]:
        stmt = (
            select(Photo)
            .where(Photo.user_id == user_id)
            .order_by(Photo.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(
        self, status: PhotoStatus, skip: int = 0, limit: int = 100
    ) -> List[Photo]:
        stmt = (
            select(Photo)
            .where(Photo.status == status)
            .order_by(Photo.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_photos_by_status(
        self, user_id: int, status: PhotoStatus, skip: int = 0, limit: int = 100
    ) -> List[Photo]:
        stmt = (
            select(Photo)
            .where(Photo.user_id == user_id, Photo.status == status)
            .order_by(Photo.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Photo]:
        stmt = select(Photo).order_by(Photo.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_photo(
        self,
        photo_id: UUID,
        storage_path: Optional[str] = None,
        status: Optional[PhotoStatus] = None,
    ) -> Optional[Photo]:
        """Update photo details."""
        update_data = {}

        if storage_path is not None:
            update_data["storage_path"] = storage_path

        if status is not None:
            update_data["status"] = status

        if not update_data:
            return await self.get_by_id(photo_id)

        stmt = update(Photo).where(Photo.id == photo_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()

        return await self.get_by_id(photo_id)

    async def delete_photo(self, photo_id: UUID) -> bool:
        photo = await self.get_by_id(photo_id)
        if not photo:
            return False

        stmt = delete(Photo).where(Photo.id == photo_id)
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def count_by_user(self, user_id: int) -> int:
        stmt = select(Photo).where(Photo.user_id == user_id)
        result = await self.db.execute(stmt)
        return len(list(result.scalars().all()))

    async def count_by_user_and_status(self, user_id: int, status: PhotoStatus) -> int:
        stmt = select(Photo).where(Photo.user_id == user_id, Photo.status == status)
        result = await self.db.execute(stmt)
        return len(list(result.scalars().all()))

    async def exists(self, photo_id: UUID) -> bool:
        photo = await self.get_by_id(photo_id)
        return photo is not None
