from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from configs.db import get_db
from configs.settings import settings
from models.user import UserCreateRequest, UserResponse, UserUpdateRequest
from services.user import UserService

router = APIRouter(prefix=f"/api/{settings.APP_VERSION}/users", tags=["Users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(get_user_service),
):
    """
    Create a new user.

    Args:
        user_data: User creation data (username, email, password)
        user_service: UserService dependency

    Returns:
        UserResponse: The created user data

    Raises:
        HTTPException 400: If username or email already exists
    """
    try:
        user = await user_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get all users with pagination.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        user_service: UserService dependency

    Returns:
        List[UserResponse]: List of users
    """
    users = await user_service.get_all_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(..., ge=1, description="User ID"),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get a user by ID.

    Args:
        user_id: The ID of the user to retrieve
        user_service: UserService dependency

    Returns:
        UserResponse: The user data

    Raises:
        HTTPException 404: If user not found
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int = Path(..., ge=1, description="User ID"),
    user_data: UserUpdateRequest = ...,
    user_service: UserService = Depends(get_user_service),
):
    """
    Update a user's information.

    Args:
        user_id: The ID of the user to update
        user_data: User update data (username, email, password - all optional)
        user_service: UserService dependency

    Returns:
        UserResponse: The updated user data

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If new username or email already exists
    """

    try:
        user = await user_service.update_user(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int = Path(..., ge=1, description="User ID"),
    user_service: UserService = Depends(get_user_service),
):
    """
    Delete a user by ID.

    Args:
        user_id: The ID of the user to delete
        user_service: UserService dependency

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: If user not found
    """

    deleted = await user_service.delete_user(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return None
