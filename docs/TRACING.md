# Google Cloud Trace Integration

This document describes the distributed tracing setup for the Photo Studio application using OpenTelemetry and Google Cloud Trace.

## Overview

The application is instrumented with OpenTelemetry to send distributed traces to Google Cloud Trace. This provides visibility into:

- **Request flows** through the FastAPI application
- **Database queries** via SQLAlchemy instrumentation
- **External API calls** (e.g., Gemini API for AI image generation)
- **Custom operations** with manual instrumentation

## Architecture

```
FastAPI App → OpenTelemetry SDK → Cloud Trace Exporter → Google Cloud Trace
```

### Automatic Instrumentation

The following components are automatically instrumented:

1. **FastAPI** - All HTTP requests and responses
2. **SQLAlchemy** - All database queries
3. **HTTPX** - All outbound HTTP requests

### Manual Instrumentation

Custom spans are added to critical operations:

- **AI Image Generation** (`services/ai_image_generator.py`)
  - `generate_image_from_text` - Text-to-image generation
  - `generate_image_from_text_and_image` - Image-to-image generation with prompt
  - Includes attributes like model name, prompt length, image size, aspect ratio

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Enable/disable tracing
ENABLE_TRACING=true

# Google Cloud Project ID (already configured)
GCS_PROJECT_ID=your-project-id

# Google Application Credentials (already configured)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Settings

Tracing is configured in `configs/settings.py`:

```python
ENABLE_TRACING: bool = True  # Set to False to disable tracing
```

## Setup

### 1. Enable Cloud Trace API

```bash
gcloud services enable cloudtrace.googleapis.com --project=YOUR_PROJECT_ID
```

### 2. Grant IAM Permissions

Ensure your service account has the `roles/cloudtrace.agent` role:

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.agent"
```

### 3. Run the Application

The tracing is automatically initialized when the application starts:

```bash
python main.py
```

You should see:
```
✅ Tracing enabled - exporting to Google Cloud Trace (Project: your-project-id)
```

## Viewing Traces

### Google Cloud Console

1. Go to [Cloud Trace](https://console.cloud.google.com/traces) in Google Cloud Console
2. Select your project
3. View trace list and timeline
4. Click on individual traces to see detailed span information

### Trace Explorer

Use the Trace Explorer to:
- Filter traces by service, latency, or time range
- Analyze latency distribution
- Identify performance bottlenecks

## Custom Instrumentation

### Adding Custom Spans

To add custom tracing to your code:

```python
from opentelemetry import trace

# Get a tracer
tracer = trace.get_tracer(__name__)

# Create a span
async def my_function():
    with tracer.start_as_current_span(
        "my_operation",
        attributes={
            "custom.attribute": "value",
            "user.id": user_id,
        }
    ) as span:
        try:
            # Your code here
            result = await some_operation()
            
            # Add more attributes
            span.set_attribute("result.size", len(result))
            span.set_attribute("success", True)
            
            return result
        except Exception as e:
            # Record exceptions
            span.set_attribute("success", False)
            span.record_exception(e)
            raise
```

### Span Attributes

Common attributes to include:

- **Operation details**: `operation.type`, `operation.name`
- **Resource identifiers**: `user.id`, `photo.id`, `album.id`
- **Performance metrics**: `data.size`, `item.count`
- **Status**: `success`, `error.message`

## Trace Attributes in AI Image Generator

The AI image generation service includes these trace attributes:

| Attribute | Description |
|-----------|-------------|
| `ai.model` | Gemini model name |
| `ai.prompt_length` | Length of the text prompt |
| `ai.aspect_ratio` | Requested aspect ratio |
| `ai.has_reference_image` | Whether a reference image was provided |
| `ai.reference_image_size_bytes` | Size of reference image |
| `ai.image_size_bytes` | Size of generated image |
| `ai.mime_type` | MIME type of generated image |
| `ai.success` | Whether generation succeeded |
| `ai.error` | Error message if failed |

## Performance Considerations

### Sampling

By default, all traces are exported. For high-traffic applications, consider implementing sampling:

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
sampler = TraceIdRatioBased(0.1)
tracer_provider = TracerProvider(sampler=sampler, resource=resource)
```

### Batch Export

Traces are exported in batches to minimize performance impact. The default configuration:
- **Max batch size**: 512 spans
- **Export interval**: 5 seconds
- **Max queue size**: 2048 spans

## Troubleshooting

### Traces Not Appearing

1. **Check API is enabled**:
   ```bash
   gcloud services list --enabled --project=YOUR_PROJECT_ID | grep cloudtrace
   ```

2. **Verify IAM permissions**:
   ```bash
   gcloud projects get-iam-policy YOUR_PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.role:roles/cloudtrace.agent"
   ```

3. **Check application logs** for tracing initialization messages

4. **Verify credentials** are properly configured

### High Latency

If tracing adds significant latency:
- Enable sampling (see Performance Considerations)
- Reduce the number of custom spans
- Check network connectivity to Google Cloud

## Resources

- [Google Cloud Trace Documentation](https://cloud.google.com/trace/docs)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Cloud Trace Python Client](https://github.com/GoogleCloudPlatform/opentelemetry-operations-python)

