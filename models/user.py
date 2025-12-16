from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.mixins import TimeStampMixin


class User(Base, TimeStampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class UserLoginRequest(BaseModel):
    email: str = Field(min_length=8, max_length=255)
    password: str = Field(min_length=8, max_length=100)


class UserLoginResponse(BaseModel):
    auth_token: str
    refresh_token: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(
        description="Refresh token to exchange for new access token"
    )


class TokenRefreshResponse(BaseModel):
    auth_token: str
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str = Field(min_length=8, max_length=255)
    username: str = Field(min_length=6, max_length=255)
    created_at: datetime
    updated_at: datetime


class UserCreateRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
    )
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=100)


class UserUpdateRequest(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=100)
    email: str | None = Field(None, min_length=5, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=100)
