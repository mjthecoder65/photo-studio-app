# Google Cloud Trace Integration - Setup Summary

## Overview

The Photo Studio application has been successfully instrumented with OpenTelemetry to send distributed traces to Google Cloud Trace. This provides comprehensive visibility into application performance and behavior.

## What Was Added

### 1. Dependencies

Added OpenTelemetry packages via Poetry:
- `opentelemetry-api` - Core OpenTelemetry API
- `opentelemetry-sdk` - OpenTelemetry SDK
- `opentelemetry-instrumentation-fastapi` - Automatic FastAPI instrumentation
- `opentelemetry-instrumentation-sqlalchemy` - Automatic SQLAlchemy instrumentation
- `opentelemetry-instrumentation-httpx` - Automatic HTTP client instrumentation
- `opentelemetry-exporter-gcp-trace` - Google Cloud Trace exporter

### 2. New Files Created

#### `configs/tracing.py`
- Main tracing configuration module
- `setup_tracing()` function to initialize OpenTelemetry
- Automatic instrumentation for FastAPI, SQLAlchemy, and HTTPX
- Google Cloud resource detection (Cloud Run, GCE, GKE)
- Batch span export to Cloud Trace

#### `docs/TRACING.md`
- Comprehensive documentation on tracing setup
- Configuration instructions
- IAM permissions requirements
- How to view traces in Cloud Console
- Custom instrumentation examples
- Troubleshooting guide

#### `examples/tracing_example.py`
- Example script demonstrating manual tracing
- Shows how to create custom spans
- Demonstrates span attributes and nested spans

#### `examples/README.md`
- Documentation for example scripts

### 3. Modified Files

#### `main.py`
- Added import for `setup_tracing`
- Calls `setup_tracing()` to initialize tracing on application startup

#### `configs/settings.py`
- Added `ENABLE_TRACING` setting (default: `True`)

#### `services/ai_image_generator.py`
- Added OpenTelemetry tracer import
- Instrumented `generate_image_from_text()` with custom spans
- Instrumented `generate_image_from_text_and_image()` with custom spans
- Added rich span attributes for AI operations:
  - Model name
  - Prompt length
  - Aspect ratio
  - Image sizes
  - Success/failure status
  - Error messages

#### `.env.example`
- Added `ENABLE_TRACING` configuration option

## Features

### Automatic Instrumentation

✅ **FastAPI** - All HTTP requests are automatically traced
- Request/response details
- HTTP status codes
- Route information

✅ **SQLAlchemy** - All database queries are automatically traced
- SQL statements
- Query duration
- Database connection info

✅ **HTTPX** - All outbound HTTP requests are automatically traced
- External API calls
- Request/response details

### Manual Instrumentation

✅ **AI Image Generation** - Custom spans for image generation operations
- Gemini API call duration
- Image generation parameters
- Success/failure tracking
- Error details

### Trace Attributes

The instrumentation includes rich attributes for filtering and analysis:

**AI Operations:**
- `ai.model` - Model name (e.g., "gemini-2.5-flash-image")
- `ai.prompt_length` - Length of text prompt
- `ai.aspect_ratio` - Requested aspect ratio
- `ai.image_size_bytes` - Size of generated image
- `ai.mime_type` - Image MIME type
- `ai.success` - Operation success status
- `ai.error` - Error message if failed

**Service Information:**
- `service.name` - "photo-studio-app"
- `service.version` - "1.0.0"
- GCP resource attributes (auto-detected)

## Setup Instructions

### 1. Enable Cloud Trace API

```bash
gcloud services enable cloudtrace.googleapis.com --project=YOUR_PROJECT_ID
```

### 2. Grant IAM Permissions

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.agent"
```

### 3. Configure Environment

Add to your `.env` file:
```bash
ENABLE_TRACING=true
GCS_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 4. Run the Application

```bash
poetry run python main.py
```

You should see:
```
✅ Tracing enabled - exporting to Google Cloud Trace (Project: your-project-id)
```

## Viewing Traces

### Cloud Console

1. Navigate to: https://console.cloud.google.com/traces/list
2. Select your project
3. Filter by service name: `photo-studio-app`
4. Click on traces to view detailed span information

### What You'll See

- **Request traces** showing the full lifecycle of HTTP requests
- **Database query spans** showing SQL execution times
- **AI generation spans** showing Gemini API call duration
- **Nested spans** showing parent-child relationships
- **Attributes** for filtering and analysis

## Benefits

1. **Performance Monitoring** - Identify slow operations and bottlenecks
2. **Error Tracking** - See exactly where errors occur in the request flow
3. **Dependency Analysis** - Understand how services interact
4. **Debugging** - Trace requests across distributed components
5. **Optimization** - Data-driven decisions for performance improvements

## Next Steps

1. **Add more custom spans** to other critical operations
2. **Set up alerts** in Cloud Monitoring for high latency
3. **Create dashboards** for key metrics
4. **Implement sampling** for high-traffic scenarios
5. **Add trace context** to logs for correlation

## Resources

- [Documentation](docs/TRACING.md) - Detailed tracing documentation
- [Example](examples/tracing_example.py) - Manual instrumentation example
- [Cloud Trace Docs](https://cloud.google.com/trace/docs)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)

