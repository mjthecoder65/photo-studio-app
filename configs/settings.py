import os
from enum import Enum
from typing import Optional

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentEnvironment(str, Enum):
    DEV = "dev"
    PROD = "prod"
    STAGING = "staging"


class Settings(BaseSettings):
    # Application Settings
    APP_ENV: str = DeploymentEnvironment.DEV
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8080
    APP_NAME: str = "Photo Studio App"
    APP_VERSION: str = "v1"

    # Google Cloud Settings
    GCS_PROJECT_ID: str
    GCS_BUCKET_NAME: str
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    FIRESTORE_COLLECTION_PHOTOS: str = "photo_metadata"

    # Secret Manager Settings
    USE_SECRET_MANAGER: bool = False  # Set to True in production

    # Database Configuration
    # In production, this will be loaded from Secret Manager
    DATABASE_URL: Optional[PostgresDsn] = None

    # JWT Configuration
    # In production, these will be loaded from Secret Manager
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gemini API Configuration
    # In production, this will be loaded from Secret Manager
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_IMAGE_MODEL: str = "gemini-2.5-flash-image"  # Nano Banana model

    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    @property
    def DEBUG(self) -> bool:
        return self.APP_ENV != DeploymentEnvironment.PROD

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )

    def load_secrets_from_secret_manager(self) -> None:
        """
        Load secrets from Google Cloud Secret Manager.

        This method should be called after Settings initialization
        when USE_SECRET_MANAGER is True.
        """
        if not self.USE_SECRET_MANAGER:
            return

        # Import here to avoid circular dependency
        from services.secret_manager import SecretManagerService

        secret_manager = SecretManagerService(project_id=self.GCS_PROJECT_ID)

        if not self.DATABASE_URL:
            try:
                db_url = secret_manager.get_secret("database-url")
                self.DATABASE_URL = PostgresDsn(db_url)
            except Exception as e:
                raise ValueError(
                    f"Failed to load DATABASE_URL from Secret Manager: {e}"
                )

        # Load JWT_SECRET_KEY from Secret Manager
        if not self.JWT_SECRET_KEY:
            try:
                self.JWT_SECRET_KEY = secret_manager.get_secret("jwt-secret-key")
            except Exception as e:
                raise ValueError(
                    f"Failed to load JWT_SECRET_KEY from Secret Manager: {e}"
                )

        # Load GEMINI_API_KEY from Secret Manager
        if not self.GEMINI_API_KEY:
            try:
                self.GEMINI_API_KEY = secret_manager.get_secret("gemini-api-key")
            except Exception as e:
                raise ValueError(
                    f"Failed to load GEMINI_API_KEY from Secret Manager: {e}"
                )


def get_settings() -> Settings:
    """
    Get application settings.

    This function initializes settings and loads secrets from Secret Manager
    if USE_SECRET_MANAGER is enabled.

    Returns:
        Settings: Application settings with secrets loaded
    """
    settings = Settings()

    # Load secrets from Secret Manager if enabled
    if settings.USE_SECRET_MANAGER:
        settings.load_secrets_from_secret_manager()

    # Validate required secrets are present
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is required")

    if not settings.JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY is required")

    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required")

    return settings


settings = get_settings()
