"""
Cloud Run Function for generating photo thumbnails.

This function is triggered when a photo is uploaded to Google Cloud Storage.
It generates a thumbnail and saves it back to GCS, then updates Firestore metadata.
"""

import io
import os
from typing import Any

import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import firestore, storage
from PIL import Image

# Configuration
THUMBNAIL_SIZES = {
    "small": (150, 150),
    "medium": (300, 300),
    "large": (600, 600),
}
THUMBNAIL_QUALITY = 85
THUMBNAIL_FORMAT = "JPEG"

# Initialize clients
storage_client = storage.Client()
firestore_client = firestore.Client()


def generate_thumbnail(
    image_bytes: bytes, size: tuple[int, int], quality: int = THUMBNAIL_QUALITY
) -> bytes:
    """
    Generate a thumbnail from image bytes.

    Args:
        image_bytes: Original image bytes
        size: Tuple of (width, height) for thumbnail
        quality: JPEG quality (1-100)

    Returns:
        bytes: Thumbnail image bytes
    """
    # Open image
    image = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA to RGB if necessary
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(
            image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None
        )
        image = background

    # Generate thumbnail (maintains aspect ratio)
    image.thumbnail(size, Image.Resampling.LANCZOS)

    # Save to bytes
    output = io.BytesIO()
    image.save(output, format=THUMBNAIL_FORMAT, quality=quality, optimize=True)
    output.seek(0)

    return output.getvalue()


def get_thumbnail_path(original_path: str, size_name: str) -> str:
    """
    Generate thumbnail path from original path.

    Args:
        original_path: Original file path (e.g., users/1/photos/uuid.jpg)
        size_name: Size name (small, medium, large)

    Returns:
        str: Thumbnail path (e.g., users/1/photos/thumbnails/uuid_small.jpg)
    """
    # Split path into parts
    parts = original_path.rsplit("/", 1)
    if len(parts) == 2:
        directory, filename = parts
    else:
        directory = ""
        filename = parts[0]

    # Split filename and extension
    name_parts = filename.rsplit(".", 1)
    if len(name_parts) == 2:
        name, ext = name_parts
    else:
        name = name_parts[0]
        ext = "jpg"

    # Create thumbnail path
    if directory:
        return f"{directory}/thumbnails/{name}_{size_name}.{ext}"
    else:
        return f"thumbnails/{name}_{size_name}.{ext}"


@functions_framework.cloud_event
def generate_photo_thumbnail(cloud_event: CloudEvent) -> None:
    """
    Cloud Run Function triggered by GCS object finalization.

    This function generates thumbnails when a photo is uploaded to GCS.

    Args:
        cloud_event: CloudEvent containing GCS event data
    """
    data: dict[str, Any] = cloud_event.data

    bucket_name = data["bucket"]
    file_path = data["name"]

    # Skip if this is already a thumbnail
    if "/thumbnails/" in file_path:
        print(f"Skipping thumbnail file: {file_path}")
        return

    # Skip if not in photos directory
    if "/photos/" not in file_path:
        print(f"Skipping non-photo file: {file_path}")
        return

    print(f"Processing photo: {file_path} from bucket: {bucket_name}")

    try:
        # Get the bucket and blob
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        # Download the image
        image_bytes = blob.download_as_bytes()
        content_type = blob.content_type or "image/jpeg"

        print(f"Downloaded image: {len(image_bytes)} bytes, type: {content_type}")

        # Generate thumbnails for each size
        thumbnail_urls = {}

        for size_name, size_dimensions in THUMBNAIL_SIZES.items():
            print(
                f"Generating {size_name} thumbnail ({size_dimensions[0]}x{size_dimensions[1]})"
            )

            # Generate thumbnail
            thumbnail_bytes = generate_thumbnail(image_bytes, size_dimensions)

            # Upload thumbnail to GCS
            thumbnail_path = get_thumbnail_path(file_path, size_name)
            thumbnail_blob = bucket.blob(thumbnail_path)

            thumbnail_blob.upload_from_string(
                thumbnail_bytes,
                content_type=content_type,
            )

            # Make thumbnail publicly accessible (optional)
            # thumbnail_blob.make_public()

            # Get public URL
            thumbnail_url = f"gs://{bucket_name}/{thumbnail_path}"
            thumbnail_urls[size_name] = thumbnail_url

            print(f"Uploaded {size_name} thumbnail to: {thumbnail_path}")

        # Extract photo ID from path (assumes format: users/{user_id}/photos/{photo_id}.ext)
        photo_id = None
        if "/photos/" in file_path:
            filename = file_path.split("/photos/")[-1]
            photo_id = filename.rsplit(".", 1)[0]  # Remove extension

        # Update Firestore metadata with thumbnail URLs
        if photo_id:
            try:
                firestore_collection = os.environ.get(
                    "FIRESTORE_COLLECTION_PHOTOS", "photo_metadata"
                )
                doc_ref = firestore_client.collection(firestore_collection).document(
                    photo_id
                )

                # Check if document exists
                doc = doc_ref.get()
                if doc.exists:
                    # Update with thumbnail URLs
                    doc_ref.update(
                        {
                            "thumbnails": thumbnail_urls,
                            "thumbnail_generated_at": firestore.SERVER_TIMESTAMP,
                        }
                    )
                    print(f"Updated Firestore metadata for photo: {photo_id}")
                else:
                    print(f"Firestore document not found for photo: {photo_id}")

            except Exception as e:
                print(f"Failed to update Firestore: {str(e)}")
                # Don't fail the function if Firestore update fails

        print(
            f"Successfully generated {len(thumbnail_urls)} thumbnails for: {file_path}"
        )

    except Exception as e:
        print(f"Error processing photo {file_path}: {str(e)}")
        raise
