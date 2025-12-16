from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.photo import Album, AlbumResponse, Photo, PhotoResponse
from repositories.album import AlbumRepository
from repositories.photo import PhotoRepository


class AlbumService:
    """Service for Album business logic."""

    def __init__(self, db: AsyncSession):
        self.repository = AlbumRepository(db)
        self.photo_repository = PhotoRepository(db)

    async def create_album(
        self, user_id: int, name: str, description: Optional[str] = None
    ) -> AlbumResponse:
        album = await self.repository.create(
            user_id=user_id, name=name, description=description
        )
        return self._to_album_response(album)

    async def get_album_by_id(self, album_id: UUID) -> Optional[AlbumResponse]:
        album = await self.repository.get_by_id(album_id)
        return self._to_album_response(album) if album else None

    async def get_user_albums(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AlbumResponse]:
        albums = await self.repository.get_by_user_id(
            user_id=user_id, skip=skip, limit=limit
        )
        return [self._to_album_response(album) for album in albums]

    async def get_all_albums(
        self, skip: int = 0, limit: int = 100
    ) -> List[AlbumResponse]:
        albums = await self.repository.get_all(skip=skip, limit=limit)
        return [self._to_album_response(album) for album in albums]

    async def update_album(
        self,
        album_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[AlbumResponse]:
        album = await self.repository.get_by_id(album_id)
        if not album:
            return None

        updated_album = await self.repository.update_album(
            album_id=album_id, name=name, description=description
        )
        return self._to_album_response(updated_album) if updated_album else None

    async def delete_album(self, album_id: UUID) -> bool:
        return await self.repository.delete_album(album_id)

    async def add_photo_to_album(
        self, album_id: UUID, photo_id: UUID, user_id: int
    ) -> bool:
        album = await self.repository.get_by_id(album_id)
        if not album or album.user_id != user_id:
            return False

        photo = await self.photo_repository.get_by_id(photo_id)
        if not photo or photo.user_id != user_id:
            return False

        if await self.repository.is_photo_in_album(album_id, photo_id):
            return False

        await self.repository.add_photo_to_album(album_id, photo_id)
        return True

    async def remove_photo_from_album(
        self, album_id: UUID, photo_id: UUID, user_id: int
    ) -> bool:
        album = await self.repository.get_by_id(album_id)
        if not album or album.user_id != user_id:
            return False

        return await self.repository.remove_photo_from_album(album_id, photo_id)

    async def get_album_photos(
        self, album_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[PhotoResponse]:
        photos = await self.repository.get_album_photos(
            album_id=album_id, skip=skip, limit=limit
        )
        return [self._to_photo_response(photo) for photo in photos]

    async def get_album_photo_count(self, album_id: UUID) -> int:
        return await self.repository.count_photos_in_album(album_id)

    async def get_user_album_count(self, user_id: int) -> int:
        return await self.repository.count_by_user(user_id)

    async def album_exists(self, album_id: UUID) -> bool:
        return await self.repository.exists(album_id)

    async def verify_album_ownership(self, album_id: UUID, user_id: int) -> bool:
        album = await self.repository.get_by_id(album_id)
        if not album:
            return False
        return album.user_id == user_id

    def _to_album_response(self, album: Album) -> AlbumResponse:
        return AlbumResponse(
            id=album.id,
            user_id=album.user_id,
            name=album.name,
            description=album.description,
            created_at=album.created_at,
            updated_at=album.updated_at,
        )

    def _to_photo_response(self, photo: Photo) -> PhotoResponse:
        return PhotoResponse(
            id=photo.id,
            user_id=photo.user_id,
            storage_path=photo.storage_path,
            status=photo.status,
            created_at=photo.created_at,
        )
