from typing import List
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from configs.db import get_db
from configs.settings import settings
from models.photo import (
    PhotoCreateRequest,
    PhotoResponse,
    PhotoStatus,
    PhotoUpdateRequest,
)
from models.user import UserResponse
from services.firestore import FirestoreService
from services.photo import PhotoService
from services.storage import StorageService

router = APIRouter(prefix=f"/api/{settings.APP_VERSION}/photos", tags=["Photos"])


def get_photo_service(db: AsyncSession = Depends(get_db)) -> PhotoService:
    return PhotoService(db)


def get_storage_service() -> StorageService:
    return StorageService()


def get_firestore_service() -> FirestoreService:
    return FirestoreService()


@router.post(
    "/upload", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED
)
async def upload_photo(
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
    storage_service: StorageService = Depends(get_storage_service),
    firestore_service: FirestoreService = Depends(get_firestore_service),
):
    """
    Upload a photo file to Google Cloud Storage and save metadata to Firestore.

    Args:
        file: Image file to upload
        current_user: Authenticated user
        photo_service: PhotoService dependency
        storage_service: StorageService dependency
        firestore_service: FirestoreService dependency

    Returns:
        PhotoResponse: The created photo record

    Raises:
        HTTPException 400: If file type is not allowed or file is too large
        HTTPException 500: If upload fails
    """

    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size {file_size} bytes exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes",
        )

    try:
        storage_path = await storage_service.upload_file(
            file=file.file,
            filename=file.filename or "photo.jpg",
            user_id=current_user.id,
            content_type=file.content_type,
        )

        photo = await photo_service.create_photo(
            user_id=current_user.id,
            storage_path=storage_path,
            status=PhotoStatus.UPLOADING,
        )

        await firestore_service.save_photo_metadata(
            photo_id=photo.id,
            user_id=current_user.id,
            storage_path=storage_path,
            filename=file.filename or "photo.jpg",
            content_type=file.content_type,
            file_size=file_size,
            status=PhotoStatus.UPLOADING.value,
            username=current_user.username,
            email=current_user.email,
        )

        await photo_service.mark_as_processed(photo.id)

        await firestore_service.update_photo_metadata(
            photo_id=photo.id,
            status=PhotoStatus.PROCESSED.value,
        )

        return photo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photo: {str(e)}",
        )


@router.post("", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_photo(
    photo_data: PhotoCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
):
    """
    Create a new photo record (without uploading a file).

    Args:
        photo_data: Photo creation data (storage_path, status)
        current_user: Authenticated user
        photo_service: PhotoService dependency

    Returns:
        PhotoResponse: The created photo
    """

    photo = await photo_service.create_photo(
        user_id=current_user.id,
        storage_path=photo_data.storage_path,
        status=photo_data.status,
    )

    return photo


@router.get("", response_model=List[PhotoResponse])
async def get_my_photos(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    status_filter: PhotoStatus | None = Query(
        None, description="Filter by photo status"
    ),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
):
    """
    Get all photos for the authenticated user with optional status filter.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        status_filter: Optional status filter
        current_user: Authenticated user
        photo_service: PhotoService dependency

    Returns:
        List[PhotoResponse]: List of user's photos
    """

    if status_filter:
        photos = await photo_service.get_user_photos_by_status(
            user_id=current_user.id,
            status=status_filter,
            skip=skip,
            limit=limit,
        )
    else:
        photos = await photo_service.get_user_photos(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
    return photos


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: UUID = Path(..., description="Photo ID"),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
):
    """
    Get a specific photo by ID.

    Args:
        photo_id: The UUID of the photo to retrieve
        current_user: Authenticated user
        photo_service: PhotoService dependency

    Returns:
        PhotoResponse: The photo data

    Raises:
        HTTPException 404: If photo not found
        HTTPException 403: If user doesn't own the photo
    """

    photo = await photo_service.get_photo_by_id(photo_id)

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID {photo_id} not found",
        )

    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this photo",
        )

    return photo


@router.get("/{photo_id}/url")
async def get_photo_url(
    photo_id: UUID = Path(..., description="Photo ID"),
    expiration: int = Query(
        3600,
        ge=60,
        le=86400,
        description="URL expiration in seconds (1 min to 24 hours)",
    ),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get a signed URL for accessing a photo.

    Args:
        photo_id: The UUID of the photo
        expiration: URL expiration time in seconds (default: 1 hour, max: 24 hours)
        current_user: Authenticated user
        photo_service: PhotoService dependency
        storage_service: StorageService dependency

    Returns:
        dict: Signed URL and expiration time

    Raises:
        HTTPException 404: If photo not found
        HTTPException 403: If user doesn't own the photo
    """

    photo = await photo_service.get_photo_by_id(photo_id)

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID {photo_id} not found",
        )

    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this photo",
        )

    signed_url = storage_service.get_signed_url(photo.storage_path, expiration)

    return {
        "photo_id": photo_id,
        "url": signed_url,
        "expires_in": expiration,
    }


@router.get("/{photo_id}/metadata")
async def get_photo_metadata(
    photo_id: UUID = Path(..., description="Photo ID"),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
    firestore_service: FirestoreService = Depends(get_firestore_service),
):
    """
    Get photo metadata from Firestore.

    Args:
        photo_id: The UUID of the photo
        current_user: Authenticated user
        photo_service: PhotoService dependency
        firestore_service: FirestoreService dependency

    Returns:
        dict: Photo metadata from Firestore

    Raises:
        HTTPException 404: If photo not found
        HTTPException 403: If user doesn't own the photo
    """

    photo = await photo_service.get_photo_by_id(photo_id)

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID {photo_id} not found",
        )

    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this photo",
        )

    metadata = await firestore_service.get_photo_metadata(photo_id)

    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metadata for photo {photo_id} not found in Firestore",
        )

    return metadata


@router.get("/{photo_id}/thumbnails")
async def get_photo_thumbnails(
    photo_id: UUID = Path(..., description="Photo ID"),
    expiration: int = Query(
        3600,
        ge=60,
        le=86400,
        description="URL expiration time in seconds (1 min to 24 hours)",
    ),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
    firestore_service: FirestoreService = Depends(get_firestore_service),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get signed URLs for photo thumbnails.

    Args:
        photo_id: The UUID of the photo
        expiration: URL expiration time in seconds
        current_user: Authenticated user
        photo_service: PhotoService dependency
        firestore_service: FirestoreService dependency
        storage_service: StorageService dependency

    Returns:
        dict: Thumbnail URLs with expiration info

    Raises:
        HTTPException 404: If photo not found or thumbnails not generated
        HTTPException 403: If user doesn't own the photo
    """

    photo = await photo_service.get_photo_by_id(photo_id)

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID {photo_id} not found",
        )

    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this photo",
        )

    # Get metadata from Firestore to check for thumbnails
    metadata = await firestore_service.get_photo_metadata(photo_id)

    if not metadata or "thumbnails" not in metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thumbnails not yet generated for photo {photo_id}. Please try again in a few moments.",
        )

    thumbnail_urls = {}
    thumbnails = metadata.get("thumbnails", {})

    for size_name, gcs_path in thumbnails.items():
        if gcs_path.startswith("gs://"):
            parts = gcs_path.replace("gs://", "").split("/", 1)
            if len(parts) == 2:
                blob_name = parts[1]
                signed_url = storage_service.get_signed_url(blob_name, expiration)
                thumbnail_urls[size_name] = signed_url

    if not thumbnail_urls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid thumbnail URLs found",
        )

    return {
        "photo_id": photo_id,
        "thumbnails": thumbnail_urls,
        "expires_in": expiration,
        "generated_at": metadata.get("thumbnail_generated_at"),
    }


@router.patch("/{photo_id}", response_model=PhotoResponse)
async def update_photo(
    photo_id: UUID = Path(..., description="Photo ID"),
    photo_data: PhotoUpdateRequest = ...,
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
):
    if not await photo_service.verify_photo_ownership(photo_id, current_user.id):
        photo_exists = await photo_service.photo_exists(photo_id)
        if not photo_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo with ID {photo_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this photo",
        )

    updated_photo = await photo_service.update_photo(
        photo_id=photo_id,
        storage_path=photo_data.storage_path,
        status=photo_data.status,
    )

    return updated_photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: UUID = Path(..., description="Photo ID"),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
    storage_service: StorageService = Depends(get_storage_service),
    firestore_service: FirestoreService = Depends(get_firestore_service),
):
    """
    Delete a photo, its file from storage, and metadata from Firestore.

    Args:
        photo_id: The UUID of the photo to delete
        current_user: Authenticated user
        photo_service: PhotoService dependency
        storage_service: StorageService dependency
        firestore_service: FirestoreService dependency

    Raises:
        HTTPException 404: If photo not found
        HTTPException 403: If user doesn't own the photo
    """

    photo = await photo_service.get_photo_by_id(photo_id)

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID {photo_id} not found",
        )

    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this photo",
        )

    await storage_service.delete_file(photo.storage_path)
    await firestore_service.delete_photo_metadata(photo_id)
    await photo_service.delete_photo(photo_id)


@router.get("/stats/count")
async def get_photo_count(
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
):
    total = await photo_service.get_user_photo_count(current_user.id)
    uploading = await photo_service.get_user_photo_count_by_status(
        current_user.id, PhotoStatus.UPLOADING
    )

    processed = await photo_service.get_user_photo_count_by_status(
        current_user.id, PhotoStatus.PROCESSED
    )

    failed = await photo_service.get_user_photo_count_by_status(
        current_user.id, PhotoStatus.FAILED
    )

    return {
        "total": total,
        "uploading": uploading,
        "processed": processed,
        "failed": failed,
    }
