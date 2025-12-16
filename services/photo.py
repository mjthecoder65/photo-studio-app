from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.photo import Photo, PhotoResponse, PhotoStatus
from repositories.photo import PhotoRepository


class PhotoService:
    """Service for Photo business logic."""

    def __init__(self, db: AsyncSession):
        self.repository = PhotoRepository(db)

    async def create_photo(
        self,
        user_id: int,
        storage_path: str,
        status: PhotoStatus = PhotoStatus.UPLOADING,
    ) -> PhotoResponse:
        photo = await self.repository.create(
            user_id=user_id, storage_path=storage_path, status=status
        )
        return self._to_photo_response(photo)

    async def get_photo_by_id(self, photo_id: UUID) -> Optional[PhotoResponse]:
        photo = await self.repository.get_by_id(photo_id)
        return self._to_photo_response(photo) if photo else None

    async def get_user_photos(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[PhotoResponse]:
        photos = await self.repository.get_by_user_id(
            user_id=user_id, skip=skip, limit=limit
        )
        return [self._to_photo_response(photo) for photo in photos]

    async def get_photos_by_status(
        self, status: PhotoStatus, skip: int = 0, limit: int = 100
    ) -> List[PhotoResponse]:
        photos = await self.repository.get_by_status(
            status=status, skip=skip, limit=limit
        )
        return [self._to_photo_response(photo) for photo in photos]

    async def get_user_photos_by_status(
        self, user_id: int, status: PhotoStatus, skip: int = 0, limit: int = 100
    ) -> List[PhotoResponse]:
        photos = await self.repository.get_user_photos_by_status(
            user_id=user_id, status=status, skip=skip, limit=limit
        )
        return [self._to_photo_response(photo) for photo in photos]

    async def get_all_photos(
        self, skip: int = 0, limit: int = 100
    ) -> List[PhotoResponse]:
        photos = await self.repository.get_all(skip=skip, limit=limit)
        return [self._to_photo_response(photo) for photo in photos]

    async def update_photo(
        self,
        photo_id: UUID,
        storage_path: Optional[str] = None,
        status: Optional[PhotoStatus] = None,
    ) -> Optional[PhotoResponse]:
        photo = await self.repository.get_by_id(photo_id)
        if not photo:
            return None

        updated_photo = await self.repository.update_photo(
            photo_id=photo_id, storage_path=storage_path, status=status
        )
        return self._to_photo_response(updated_photo) if updated_photo else None

    async def delete_photo(self, photo_id: UUID) -> bool:
        return await self.repository.delete_photo(photo_id)

    async def mark_as_processed(self, photo_id: UUID) -> Optional[PhotoResponse]:
        return await self.update_photo(photo_id=photo_id, status=PhotoStatus.PROCESSED)

    async def mark_as_failed(self, photo_id: UUID) -> Optional[PhotoResponse]:
        return await self.update_photo(photo_id=photo_id, status=PhotoStatus.FAILED)

    async def get_user_photo_count(self, user_id: int) -> int:
        return await self.repository.count_by_user(user_id)

    async def get_user_photo_count_by_status(
        self, user_id: int, status: PhotoStatus
    ) -> int:
        return await self.repository.count_by_user_and_status(user_id, status)

    async def photo_exists(self, photo_id: UUID) -> bool:
        return await self.repository.exists(photo_id)

    async def verify_photo_ownership(self, photo_id: UUID, user_id: int) -> bool:
        photo = await self.repository.get_by_id(photo_id)
        if not photo:
            return False
        return photo.user_id == user_id

    def _to_photo_response(self, photo: Photo) -> PhotoResponse:
        return PhotoResponse(
            id=photo.id,
            user_id=photo.user_id,
            storage_path=photo.storage_path,
            status=photo.status,
            created_at=photo.created_at,
        )
