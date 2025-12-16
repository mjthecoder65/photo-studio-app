#!/bin/bash

# Deployment script for thumbnail generator Cloud Run function
# This script deploys the function and sets up the GCS trigger

set -e

# Configuration
PROJECT_ID="${GCS_PROJECT_ID:-your-project-id}"
REGION="${REGION:-us-central1}"
FUNCTION_NAME="photo-thumbnail-generator"
BUCKET_NAME="${GCS_BUCKET_NAME:-your-bucket-name}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-photo-uploader@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "Deploying thumbnail generator function..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Function: $FUNCTION_NAME"
echo "Bucket: $BUCKET_NAME"

# Build and deploy the Cloud Run function
gcloud run deploy $FUNCTION_NAME \
  --source . \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --service-account $SERVICE_ACCOUNT \
  --set-env-vars "FIRESTORE_COLLECTION_PHOTOS=photo_metadata" \
  --memory 512Mi \
  --timeout 300s \
  --max-instances 10 \
  --min-instances 0

# Get the service URL
SERVICE_URL=$(gcloud run services describe $FUNCTION_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo "Service deployed at: $SERVICE_URL"

# Create Eventarc trigger for GCS object finalization
TRIGGER_NAME="${FUNCTION_NAME}-trigger"

echo "Creating Eventarc trigger..."

gcloud eventarc triggers create $TRIGGER_NAME \
  --location=$REGION \
  --project=$PROJECT_ID \
  --destination-run-service=$FUNCTION_NAME \
  --destination-run-region=$REGION \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=$BUCKET_NAME" \
  --service-account=$SERVICE_ACCOUNT

echo "Deployment complete!"
echo ""
echo "The function will now be triggered automatically when photos are uploaded to gs://$BUCKET_NAME"
echo ""
echo "To test manually, upload a photo:"
echo "  gsutil cp test-image.jpg gs://$BUCKET_NAME/users/1/photos/test.jpg"
echo ""
echo "To view logs:"
echo "  gcloud run services logs read $FUNCTION_NAME --region $REGION --project $PROJECT_ID"

