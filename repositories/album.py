from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.photo import Album, AlbumPhoto, Photo


class AlbumRepository:
    """Repository for Album database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, user_id: int, name: str, description: Optional[str] = None
    ) -> Album:
        album = Album(user_id=user_id, name=name, description=description)
        self.db.add(album)
        await self.db.commit()
        await self.db.refresh(album)
        return album

    async def get_by_id(self, album_id: UUID) -> Optional[Album]:
        stmt = select(Album).where(Album.id == album_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Album]:
        stmt = (
            select(Album)
            .where(Album.user_id == user_id)
            .order_by(Album.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Album]:
        stmt = select(Album).order_by(Album.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_album(
        self,
        album_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Album]:
        update_data = {}

        if name is not None:
            update_data["name"] = name

        if description is not None:
            update_data["description"] = description

        if not update_data:
            return await self.get_by_id(album_id)

        stmt = update(Album).where(Album.id == album_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()

        return await self.get_by_id(album_id)

    async def delete_album(self, album_id: UUID) -> bool:
        album = await self.get_by_id(album_id)
        if not album:
            return False

        stmt = delete(Album).where(Album.id == album_id)
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def add_photo_to_album(self, album_id: UUID, photo_id: UUID) -> AlbumPhoto:
        album_photo = AlbumPhoto(album_id=album_id, photo_id=photo_id)
        self.db.add(album_photo)
        await self.db.commit()
        await self.db.refresh(album_photo)
        return album_photo

    async def remove_photo_from_album(self, album_id: UUID, photo_id: UUID) -> bool:
        stmt = delete(AlbumPhoto).where(
            AlbumPhoto.album_id == album_id, AlbumPhoto.photo_id == photo_id
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def get_album_photos(
        self, album_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Photo]:
        stmt = (
            select(Photo)
            .join(AlbumPhoto, AlbumPhoto.photo_id == Photo.id)
            .where(AlbumPhoto.album_id == album_id)
            .order_by(AlbumPhoto.added_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def is_photo_in_album(self, album_id: UUID, photo_id: UUID) -> bool:
        stmt = select(AlbumPhoto).where(
            AlbumPhoto.album_id == album_id, AlbumPhoto.photo_id == photo_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_photos_in_album(self, album_id: UUID) -> int:
        stmt = select(AlbumPhoto).where(AlbumPhoto.album_id == album_id)
        result = await self.db.execute(stmt)
        return len(list(result.scalars().all()))

    async def count_by_user(self, user_id: int) -> int:
        stmt = select(Album).where(Album.user_id == user_id)
        result = await self.db.execute(stmt)
        return len(list(result.scalars().all()))

    async def exists(self, album_id: UUID) -> bool:
        album = await self.get_by_id(album_id)
        return album is not None
