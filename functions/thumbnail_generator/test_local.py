"""
Local testing script for thumbnail generator function.

This script simulates a GCS CloudEvent and tests the thumbnail generation locally.
"""

import json
from datetime import datetime

from cloudevents.http import CloudEvent


def create_test_event(bucket_name: str, file_path: str) -> CloudEvent:
    """
    Create a test CloudEvent for GCS object finalization.

    Args:
        bucket_name: GCS bucket name
        file_path: Path to the file in the bucket

    Returns:
        CloudEvent: Test event
    """
    attributes = {
        "type": "google.cloud.storage.object.v1.finalized",
        "source": f"//storage.googleapis.com/projects/_/buckets/{bucket_name}",
        "id": "test-event-id",
        "time": datetime.utcnow().isoformat() + "Z",
        "specversion": "1.0",
    }

    data = {
        "bucket": bucket_name,
        "name": file_path,
        "contentType": "image/jpeg",
        "size": "1024000",
        "timeCreated": datetime.utcnow().isoformat() + "Z",
        "updated": datetime.utcnow().isoformat() + "Z",
    }

    return CloudEvent(attributes, data)


def test_thumbnail_generation():
    """Test the thumbnail generation function locally."""
    import os

    # Set environment variables for testing
    os.environ["FIRESTORE_COLLECTION_PHOTOS"] = "photo_metadata"
    os.environ["GCS_PROJECT_ID"] = "your-project-id"

    # Import the function
    from main import generate_photo_thumbnail

    # Create test event
    bucket_name = "your-bucket-name"
    file_path = "users/1/photos/test-photo-id.jpg"

    event = create_test_event(bucket_name, file_path)

    print("Testing thumbnail generation...")
    print(f"Bucket: {bucket_name}")
    print(f"File: {file_path}")
    print()

    try:
        # Call the function
        generate_photo_thumbnail(event)
        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("Thumbnail Generator - Local Test")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
    print("2. Upload a test image to GCS first")
    print("3. Update bucket_name and file_path in this script")
    print()
    print("=" * 60)
    print()

    test_thumbnail_generation()

