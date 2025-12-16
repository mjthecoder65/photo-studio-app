from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth import create_access_token, create_refresh_token, decode_token
from configs.db import get_db
from configs.settings import settings
from models.user import (
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserCreateRequest,
    UserLoginRequest,
    UserLoginResponse,
    UserResponse,
)
from services.user import UserService

router = APIRouter(prefix=f"/api/{settings.APP_VERSION}/auth", tags=["Authentication"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency to get UserService instance."""
    return UserService(db)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(get_user_service),
):
    """
    Register a new user.

    Args:
        user_data: User registration data (username, email, password)
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


@router.post("/login", response_model=UserLoginResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: UserLoginRequest,
    user_service: UserService = Depends(get_user_service),
):
    """
    Authenticate a user and return JWT tokens.

    Args:
        login_data: User login credentials (email, password)
        user_service: UserService dependency

    Returns:
        UserLoginResponse: Access and refresh tokens

    Raises:
        HTTPException 401: If credentials are invalid
    """
    user = await user_service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens with user data
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return UserLoginResponse(
        auth_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh-token",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    token_data: TokenRefreshRequest,
    user_service: UserService = Depends(get_user_service),
):
    """
    Refresh access token using a valid refresh token.

    Args:
        token_data: Request containing the refresh token
        user_service: UserService dependency

    Returns:
        TokenRefreshResponse: New access and refresh tokens

    Raises:
        HTTPException 401: If refresh token is invalid or expired
        HTTPException 404: If user no longer exists
    """
    # Decode and validate the refresh token
    payload = decode_token(token_data.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Create new tokens
    new_token_data = {"sub": str(user.id), "email": user.email}
    new_access_token = create_access_token(data=new_token_data)
    new_refresh_token = create_refresh_token(data=new_token_data)

    return TokenRefreshResponse(
        auth_token=new_access_token,
        refresh_token=new_refresh_token,
    )
