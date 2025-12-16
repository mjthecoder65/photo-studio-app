# AI Photo Generation with Gemini (Nano Banana)

This document describes the AI-powered photo generation feature using Google's Gemini API (Nano Banana).

## Overview

The application now supports generating photos from text prompts using Google's Gemini 2.5 Flash Image model (also known as "Nano Banana"). Generated images are automatically:
- Uploaded to Google Cloud Storage
- Saved to PostgreSQL database
- Metadata stored in Cloud Firestore
- Thumbnails generated via Cloud Run function

## Features

### 1. Text-to-Image Generation
Generate images from text descriptions with customizable aspect ratios.

### 2. Image-to-Image Generation
Modify existing images based on text prompts (reference image + text).

### 3. Multiple Aspect Ratios
Support for 10 different aspect ratios:
- `1:1` - Square (1024x1024)
- `2:3` - Portrait (832x1248)
- `3:2` - Landscape (1248x832)
- `3:4` - Portrait (864x1184)
- `4:3` - Landscape (1184x864)
- `4:5` - Portrait (896x1152)
- `5:4` - Landscape (1152x896)
- `9:16` - Vertical (768x1344)
- `16:9` - Horizontal (1344x768)
- `21:9` - Ultra-wide (1536x672)

### 4. SynthID Watermarking
All generated images include Google's SynthID watermark for AI-generated content identification.

## API Endpoints

### Generate Photo from Text

**Endpoint:** `POST /api/v1/ai-photos/generate`

**Authentication:** Required (JWT Bearer token)

**Request Body (multipart/form-data):**
```
prompt: string (required) - Text description of the image to generate
aspect_ratio: string (optional, default: "1:1") - Aspect ratio for the image
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai-photos/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "prompt=A serene mountain landscape at sunset with a lake reflection" \
  -F "aspect_ratio=16:9"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "storage_path": "users/1/photos/550e8400-e29b-41d4-a716-446655440000.png",
  "status": "processed",
  "created_at": "2025-12-16T10:30:00Z"
}
```

### Generate Photo from Reference Image

**Endpoint:** `POST /api/v1/ai-photos/generate-from-reference`

**Authentication:** Required (JWT Bearer token)

**Request Body (multipart/form-data):**
```
prompt: string (required) - Text description for image modification
reference_image: file (required) - Reference image file
aspect_ratio: string (optional, default: "1:1") - Aspect ratio for the image
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai-photos/generate-from-reference" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "prompt=Make it look like a watercolor painting" \
  -F "reference_image=@photo.jpg" \
  -F "aspect_ratio=4:3"
```

### Get Supported Aspect Ratios

**Endpoint:** `GET /api/v1/ai-photos/supported-aspect-ratios`

**Authentication:** Not required

**Response:**
```json
{
  "supported_aspect_ratios": [
    {"ratio": "1:1", "description": "Square (1024x1024)"},
    {"ratio": "16:9", "description": "Horizontal (1344x768)"},
    ...
  ]
}
```

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
```

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key and add it to your `.env` file

## Firestore Metadata

AI-generated photos include additional metadata in Firestore:

```json
{
  "photo_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "storage_path": "users/1/photos/550e8400-e29b-41d4-a716-446655440000.png",
  "filename": "ai_generated_16x9.png",
  "content_type": "image/png",
  "file_size": 1234567,
  "status": "processed",
  "username": "john_doe",
  "email": "john@example.com",
  "ai_generated": true,
  "ai_prompt": "A serene mountain landscape at sunset",
  "ai_aspect_ratio": "16:9",
  "ai_model": "gemini-2.5-flash-image",
  "created_at": "2025-12-16T10:30:00Z"
}
```

## Architecture

```
User Request
    ↓
FastAPI Endpoint (/api/v1/ai-photos/generate)
    ↓
AIImageGeneratorService (calls Gemini API)
    ↓
StorageService (uploads to GCS)
    ↓
PhotoService (saves to PostgreSQL)
    ↓
FirestoreService (saves metadata)
    ↓
Cloud Run Function (generates thumbnails)
    ↓
Response to User
```

## Error Handling

The API returns appropriate HTTP status codes:

- `201 Created` - Photo generated successfully
- `400 Bad Request` - Invalid aspect ratio or file type
- `401 Unauthorized` - Missing or invalid JWT token
- `500 Internal Server Error` - Generation or upload failed

## Limitations

1. **Rate Limits:** Gemini API has rate limits based on your API key tier
2. **Image Size:** Generated images are limited to the resolutions specified by aspect ratio
3. **Content Policy:** Gemini API enforces content safety policies
4. **Cost:** Each generation consumes API quota (check Google AI pricing)

## Best Practices

1. **Prompt Engineering:** Be specific and descriptive in your prompts
2. **Aspect Ratio Selection:** Choose aspect ratios appropriate for your use case
3. **Error Handling:** Implement retry logic for transient failures
4. **Cost Management:** Monitor API usage and implement rate limiting
5. **Content Moderation:** Review generated content for appropriateness

## Future Enhancements

- Batch generation support
- Style presets (e.g., "photorealistic", "artistic", "cartoon")
- Negative prompts (specify what NOT to include)
- Image upscaling
- Advanced editing features
- Generation history and favorites

