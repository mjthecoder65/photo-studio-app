from enum import Enum

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentEnvironment(str, Enum):
    DEV = "dev"
    PROD = "prod"
    STAGING = "staging"


class Settings(BaseSettings):
    APP_ENV: str = DeploymentEnvironment.DEV
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8080
    APP_NAME: str = "Demo-App Service"
    APP_VERSION: str = "v1"
    DATABASE_URL: PostgresDsn
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int
    GCS_BUCKET_NAME: str
    GCS_PROJECT_ID: str
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    FIRESTORE_COLLECTION_PHOTOS: str = "photo_metadata"
    GEMINI_API_KEY: str
    GEMINI_IMAGE_MODEL: str = "gemini-2.5-flash-image"  # Nano Banana model

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


settings = Settings()
