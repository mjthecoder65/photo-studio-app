import os
from datetime import timedelta
from typing import BinaryIO
from uuid import uuid4

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from configs.settings import settings


class StorageService:
    """Service for Google Cloud Storage operations."""

    def __init__(self):
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            self.client = storage.Client.from_service_account_json(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
        else:
            self.client = storage.Client(project=settings.GCS_PROJECT_ID)

        self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)

    def _generate_unique_filename(self, original_filename: str, user_id: int) -> str:
        _, ext = os.path.splitext(original_filename)

        unique_id = uuid4()
        return f"users/{user_id}/photos/{unique_id}{ext}"

    async def upload_file(
        self, file: BinaryIO, filename: str, user_id: int, content_type: str
    ) -> str:
        try:
            blob_name = self._generate_unique_filename(filename, user_id)

            blob = self.bucket.blob(blob_name)
            blob.upload_from_file(file, content_type=content_type, rewind=True)

            return blob_name
        except GoogleCloudError as e:
            raise Exception(f"Failed to upload file to GCS: {str(e)}")

    async def delete_file(self, blob_name: str) -> bool:
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except GoogleCloudError:
            return False

    def get_signed_url(self, blob_name: str, expiration: int = 3600) -> str:

        blob = self.bucket.blob(blob_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="GET",
        )
        return url

    def get_public_url(self, blob_name: str) -> str:
        blob = self.bucket.blob(blob_name)
        return blob.public_url

    async def file_exists(self, blob_name: str) -> bool:
        blob = self.bucket.blob(blob_name)
        return blob.exists()
