from typing import Any, Optional
from uuid import UUID

from google.cloud import firestore
from google.cloud.exceptions import GoogleCloudError

from configs.settings import settings


class FirestoreService:
    """Service for Cloud Firestore operations."""

    def __init__(self):
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            self.client = firestore.Client.from_service_account_json(
                settings.GOOGLE_APPLICATION_CREDENTIALS,
                project=settings.GCS_PROJECT_ID,
            )
        else:
            self.client = firestore.Client(project=settings.GCS_PROJECT_ID)

    async def save_photo_metadata(
        self,
        photo_id: UUID,
        user_id: int,
        storage_path: str,
        filename: str,
        content_type: str,
        file_size: int,
        status: str = "uploading",
        **additional_metadata: Any,
    ) -> bool:
        """
        Save photo metadata to Firestore.

        Args:
            photo_id: UUID of the photo
            user_id: ID of the user who uploaded the photo
            storage_path: GCS storage path
            filename: Original filename
            content_type: MIME type of the file
            file_size: Size of the file in bytes
            status: Processing status
            **additional_metadata: Any additional metadata to store

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            doc_ref = self.client.collection(
                settings.FIRESTORE_COLLECTION_PHOTOS
            ).document(str(photo_id))

            metadata = {
                "photo_id": str(photo_id),
                "user_id": user_id,
                "storage_path": storage_path,
                "filename": filename,
                "content_type": content_type,
                "file_size": file_size,
                "status": status,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
                **additional_metadata,
            }

            doc_ref.set(metadata)
            return True
        except GoogleCloudError as e:
            print(f"Failed to save metadata to Firestore: {str(e)}")
            return False

    async def get_photo_metadata(self, photo_id: UUID) -> Optional[dict]:
        """
        Get photo metadata from Firestore.

        Args:
            photo_id: UUID of the photo

        Returns:
            Optional[dict]: Photo metadata or None if not found
        """
        try:
            doc_ref = self.client.collection(
                settings.FIRESTORE_COLLECTION_PHOTOS
            ).document(str(photo_id))
            doc = doc_ref.get()

            if doc.exists:
                return doc.to_dict()
            return None
        except GoogleCloudError as e:
            print(f"Failed to get metadata from Firestore: {str(e)}")
            return None

    async def update_photo_metadata(self, photo_id: UUID, **updates: Any) -> bool:
        """
        Update photo metadata in Firestore.

        Args:
            photo_id: UUID of the photo
            **updates: Fields to update

        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            doc_ref = self.client.collection(
                settings.FIRESTORE_COLLECTION_PHOTOS
            ).document(str(photo_id))

            updates["updated_at"] = firestore.SERVER_TIMESTAMP
            doc_ref.update(updates)
            return True
        except GoogleCloudError as e:
            print(f"Failed to update metadata in Firestore: {str(e)}")
            return False

    async def delete_photo_metadata(self, photo_id: UUID) -> bool:
        """
        Delete photo metadata from Firestore.

        Args:
            photo_id: UUID of the photo

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            doc_ref = self.client.collection(
                settings.FIRESTORE_COLLECTION_PHOTOS
            ).document(str(photo_id))
            doc_ref.delete()
            return True
        except GoogleCloudError as e:
            print(f"Failed to delete metadata from Firestore: {str(e)}")
            return False

    async def get_user_photos_metadata(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """
        Get all photo metadata for a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            list[dict]: List of photo metadata
        """
        try:
            query = (
                self.client.collection(settings.FIRESTORE_COLLECTION_PHOTOS)
                .where("user_id", "==", user_id)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .offset(offset)
            )

            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except GoogleCloudError as e:
            print(f"Failed to get user photos metadata from Firestore: {str(e)}")
            return []
