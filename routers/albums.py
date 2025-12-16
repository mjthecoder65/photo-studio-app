from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from configs.db import get_db
from configs.settings import settings
from models.photo import (
    AlbumCreateRequest,
    AlbumResponse,
    AlbumUpdateRequest,
    PhotoResponse,
)
from models.user import UserResponse
from services.album import AlbumService

router = APIRouter(prefix=f"/api/{settings.APP_VERSION}/albums", tags=["Albums"])


def get_album_service(db: AsyncSession = Depends(get_db)) -> AlbumService:
    return AlbumService(db)


@router.post("", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
async def create_album(
    album_data: AlbumCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Create a new album for the authenticated user.

    Args:
        album_data: Album creation data (name, description)
        current_user: Authenticated user
        album_service: AlbumService dependency

    Returns:
        AlbumResponse: The created album
    """
    album = await album_service.create_album(
        user_id=current_user.id,
        name=album_data.name,
        description=album_data.description,
    )
    return album


@router.get("", response_model=List[AlbumResponse])
async def get_my_albums(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Get all albums for the authenticated user.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        current_user: Authenticated user
        album_service: AlbumService dependency

    Returns:
        List[AlbumResponse]: List of user's albums
    """
    albums = await album_service.get_user_albums(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return albums


@router.get("/{album_id}", response_model=AlbumResponse)
async def get_album(
    album_id: UUID = Path(..., description="Album ID"),
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Get a specific album by ID.

    Args:
        album_id: The UUID of the album to retrieve
        current_user: Authenticated user
        album_service: AlbumService dependency

    Returns:
        AlbumResponse: The album data

    Raises:
        HTTPException 404: If album not found
        HTTPException 403: If user doesn't own the album
    """
    album = await album_service.get_album_by_id(album_id)

    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Album with ID {album_id} not found",
        )

    # Verify ownership
    if album.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this album",
        )

    return album


@router.patch("/{album_id}", response_model=AlbumResponse)
async def update_album(
    album_id: UUID = Path(..., description="Album ID"),
    album_data: AlbumUpdateRequest = ...,
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Update an album's details.

    Args:
        album_id: The UUID of the album to update
        album_data: Album update data
        current_user: Authenticated user
        album_service: AlbumService dependency

    Returns:
        AlbumResponse: The updated album

    Raises:
        HTTPException 404: If album not found
        HTTPException 403: If user doesn't own the album
    """
    # Verify ownership
    if not await album_service.verify_album_ownership(album_id, current_user.id):
        album_exists = await album_service.album_exists(album_id)
        if not album_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Album with ID {album_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this album",
        )

    updated_album = await album_service.update_album(
        album_id=album_id,
        name=album_data.name,
        description=album_data.description,
    )

    return updated_album


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_album(
    album_id: UUID = Path(..., description="Album ID"),
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Delete an album.

    Args:
        album_id: The UUID of the album to delete
        current_user: Authenticated user
        album_service: AlbumService dependency

    Raises:
        HTTPException 404: If album not found
        HTTPException 403: If user doesn't own the album
    """
    # Verify ownership
    if not await album_service.verify_album_ownership(album_id, current_user.id):
        album_exists = await album_service.album_exists(album_id)
        if not album_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Album with ID {album_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this album",
        )

    await album_service.delete_album(album_id)


@router.get("/{album_id}/photos", response_model=List[PhotoResponse])
async def get_album_photos(
    album_id: UUID = Path(..., description="Album ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Get all photos in an album.

    Args:
        album_id: The UUID of the album
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        current_user: Authenticated user
        album_service: AlbumService dependency

    Returns:
        List[PhotoResponse]: List of photos in the album

    Raises:
        HTTPException 404: If album not found
        HTTPException 403: If user doesn't own the album
    """

    if not await album_service.verify_album_ownership(album_id, current_user.id):
        album_exists = await album_service.album_exists(album_id)
        if not album_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Album with ID {album_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this album",
        )

    photos = await album_service.get_album_photos(
        album_id=album_id,
        skip=skip,
        limit=limit,
    )
    return photos


@router.post("/{album_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_photo_to_album(
    album_id: UUID = Path(..., description="Album ID"),
    photo_id: UUID = Path(..., description="Photo ID"),
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Add a photo to an album.

    Args:
        album_id: The UUID of the album
        photo_id: The UUID of the photo to add
        current_user: Authenticated user
        album_service: AlbumService dependency

    Raises:
        HTTPException 404: If album or photo not found
        HTTPException 403: If user doesn't own the album or photo
        HTTPException 400: If photo is already in the album
    """
    success = await album_service.add_photo_to_album(
        album_id=album_id,
        photo_id=photo_id,
        user_id=current_user.id,
    )

    if not success:
        if not await album_service.verify_album_ownership(album_id, current_user.id):
            album_exists = await album_service.album_exists(album_id)
            if not album_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Album with ID {album_id} not found",
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this album",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo not found, you don't own it, or it's already in the album",
        )


@router.delete("/{album_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_photo_from_album(
    album_id: UUID = Path(..., description="Album ID"),
    photo_id: UUID = Path(..., description="Photo ID"),
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Remove a photo from an album.

    Args:
        album_id: The UUID of the album
        photo_id: The UUID of the photo to remove
        current_user: Authenticated user
        album_service: AlbumService dependency

    Raises:
        HTTPException 404: If album not found or photo not in album
        HTTPException 403: If user doesn't own the album
    """
    # Verify ownership
    if not await album_service.verify_album_ownership(album_id, current_user.id):
        album_exists = await album_service.album_exists(album_id)
        if not album_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Album with ID {album_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this album",
        )

    success = await album_service.remove_photo_from_album(
        album_id=album_id,
        photo_id=photo_id,
        user_id=current_user.id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID {photo_id} not found in album",
        )


@router.get("/stats/count")
async def get_album_count(
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Get album count for the authenticated user.

    Args:
        current_user: Authenticated user
        album_service: AlbumService dependency

    Returns:
        dict: Album count
    """
    count = await album_service.get_user_album_count(current_user.id)
    return {"total": count}


@router.get("/{album_id}/stats/count")
async def get_album_photo_count(
    album_id: UUID = Path(..., description="Album ID"),
    current_user: UserResponse = Depends(get_current_user),
    album_service: AlbumService = Depends(get_album_service),
):
    """
    Get photo count for a specific album.

    Args:
        album_id: The UUID of the album
        current_user: Authenticated user
        album_service: AlbumService dependency

    Returns:
        dict: Photo count in the album

    Raises:
        HTTPException 404: If album not found
        HTTPException 403: If user doesn't own the album
    """

    if not await album_service.verify_album_ownership(album_id, current_user.id):
        album_exists = await album_service.album_exists(album_id)
        if not album_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Album with ID {album_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this album",
        )

    count = await album_service.get_album_photo_count(album_id)
    return {"total": count}
