# Photo Thumbnail Generator - Cloud Run Function

This Cloud Run function automatically generates thumbnails when photos are uploaded to Google Cloud Storage.

## Features

- **Automatic Trigger**: Triggered by GCS object finalization events
- **Multiple Sizes**: Generates small (150x150), medium (300x300), and large (600x600) thumbnails
- **Aspect Ratio Preservation**: Maintains original aspect ratio
- **Format Conversion**: Handles RGBA, LA, and P mode images
- **Firestore Integration**: Updates photo metadata with thumbnail URLs
- **Optimized**: Uses Pillow with LANCZOS resampling for high-quality thumbnails

## Architecture

```
Photo Upload → GCS → Eventarc → Cloud Run Function → Generate Thumbnails → Update Firestore
```

## Thumbnail Sizes

| Size   | Dimensions | Use Case              |
|--------|------------|-----------------------|
| Small  | 150x150    | List views, avatars   |
| Medium | 300x300    | Grid views, previews  |
| Large  | 600x600    | Detail views, modals  |

## File Structure

```
users/{user_id}/photos/{photo_id}.jpg          # Original photo
users/{user_id}/photos/thumbnails/{photo_id}_small.jpg   # Small thumbnail
users/{user_id}/photos/thumbnails/{photo_id}_medium.jpg  # Medium thumbnail
users/{user_id}/photos/thumbnails/{photo_id}_large.jpg   # Large thumbnail
```

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **APIs Enabled**:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable eventarc.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable firestore.googleapis.com
   ```

3. **Service Account** with permissions:
   - `roles/storage.objectAdmin` - Read/write GCS objects
   - `roles/datastore.user` - Update Firestore documents
   - `roles/eventarc.eventReceiver` - Receive Eventarc events

4. **Environment Variables**:
   ```bash
   export GCS_PROJECT_ID="your-project-id"
   export GCS_BUCKET_NAME="your-bucket-name"
   export REGION="us-central1"
   export SERVICE_ACCOUNT="photo-uploader@your-project-id.iam.gserviceaccount.com"
   ```

## Deployment

### Option 1: Using the deployment script

```bash
# Make the script executable
chmod +x deploy.sh

# Set environment variables
export GCS_PROJECT_ID="your-project-id"
export GCS_BUCKET_NAME="your-bucket-name"
export REGION="us-central1"

# Deploy
./deploy.sh
```

### Option 2: Manual deployment

```bash
# Deploy Cloud Run service
gcloud run deploy photo-thumbnail-generator \
  --source . \
  --region us-central1 \
  --project your-project-id \
  --platform managed \
  --allow-unauthenticated \
  --service-account photo-uploader@your-project-id.iam.gserviceaccount.com \
  --set-env-vars "FIRESTORE_COLLECTION_PHOTOS=photo_metadata" \
  --memory 512Mi \
  --timeout 300s

# Create Eventarc trigger
gcloud eventarc triggers create photo-thumbnail-generator-trigger \
  --location=us-central1 \
  --project=your-project-id \
  --destination-run-service=photo-thumbnail-generator \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=your-bucket-name" \
  --service-account=photo-uploader@your-project-id.iam.gserviceaccount.com
```

## Testing

### Test locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally with functions-framework
functions-framework --target=generate_photo_thumbnail --signature-type=cloudevent --debug
```

### Test in production

```bash
# Upload a test photo
gsutil cp test-image.jpg gs://your-bucket-name/users/1/photos/test-photo-id.jpg

# View logs
gcloud run services logs read photo-thumbnail-generator \
  --region us-central1 \
  --project your-project-id \
  --limit 50

# Check if thumbnails were created
gsutil ls gs://your-bucket-name/users/1/photos/thumbnails/
```

## Firestore Metadata Update

The function updates the Firestore document with thumbnail URLs:

```json
{
  "photo_id": "test-photo-id",
  "thumbnails": {
    "small": "gs://bucket/users/1/photos/thumbnails/test-photo-id_small.jpg",
    "medium": "gs://bucket/users/1/photos/thumbnails/test-photo-id_medium.jpg",
    "large": "gs://bucket/users/1/photos/thumbnails/test-photo-id_large.jpg"
  },
  "thumbnail_generated_at": "2025-12-16T10:30:05Z"
}
```

## Monitoring

```bash
# View function logs
gcloud run services logs read photo-thumbnail-generator --region us-central1

# View Eventarc trigger status
gcloud eventarc triggers describe photo-thumbnail-generator-trigger --location us-central1

# Monitor function metrics
gcloud monitoring dashboards list --filter="displayName:photo-thumbnail-generator"
```

## Troubleshooting

### Function not triggering

1. Check Eventarc trigger status:
   ```bash
   gcloud eventarc triggers describe photo-thumbnail-generator-trigger --location us-central1
   ```

2. Verify service account permissions:
   ```bash
   gcloud projects get-iam-policy your-project-id \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:photo-uploader@your-project-id.iam.gserviceaccount.com"
   ```

3. Check function logs for errors:
   ```bash
   gcloud run services logs read photo-thumbnail-generator --region us-central1 --limit 100
   ```

### Thumbnails not generated

- Check if the file path contains `/photos/` (required)
- Verify the image format is supported (JPEG, PNG, GIF, WebP)
- Check function memory limits (increase if needed)

### Firestore not updating

- Verify `FIRESTORE_COLLECTION_PHOTOS` environment variable
- Check service account has `roles/datastore.user` permission
- Ensure photo_id matches the Firestore document ID

## Cost Optimization

- **Min instances**: Set to 0 to avoid idle costs
- **Max instances**: Limit concurrent executions
- **Memory**: 512Mi is sufficient for most images
- **Timeout**: 300s allows processing large images

## Customization

### Change thumbnail sizes

Edit `THUMBNAIL_SIZES` in `main.py`:

```python
THUMBNAIL_SIZES = {
    "tiny": (50, 50),
    "small": (150, 150),
    "medium": (300, 300),
    "large": (600, 600),
    "xlarge": (1200, 1200),
}
```

### Change image quality

Edit `THUMBNAIL_QUALITY` in `main.py`:

```python
THUMBNAIL_QUALITY = 90  # Higher quality, larger file size
```

### Make thumbnails public

Uncomment in `main.py`:

```python
thumbnail_blob.make_public()
```

## Security

- Function uses service account authentication
- Eventarc trigger is scoped to specific bucket
- Thumbnails inherit bucket's IAM permissions
- No public access by default

