# Tracing Quick Reference

## Quick Start

### Enable Tracing

```bash
# In .env file
ENABLE_TRACING=true
GCS_PROJECT_ID=your-project-id
```

### View Traces

```bash
# Open Cloud Trace in browser
https://console.cloud.google.com/traces/list?project=YOUR_PROJECT_ID
```

## Adding Custom Spans

### Basic Span

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def my_function():
    with tracer.start_as_current_span("operation_name"):
        # Your code here
        result = await do_something()
        return result
```

### Span with Attributes

```python
async def process_photo(photo_id: str, user_id: int):
    with tracer.start_as_current_span(
        "process_photo",
        attributes={
            "photo.id": photo_id,
            "user.id": user_id,
        }
    ) as span:
        # Your code here
        photo = await get_photo(photo_id)
        
        # Add more attributes
        span.set_attribute("photo.size_bytes", photo.size)
        span.set_attribute("photo.format", photo.format)
        
        return photo
```

### Nested Spans

```python
async def complex_operation():
    with tracer.start_as_current_span("complex_operation") as parent_span:
        # First sub-operation
        with tracer.start_as_current_span("fetch_data"):
            data = await fetch_data()
        
        # Second sub-operation
        with tracer.start_as_current_span("process_data"):
            result = await process_data(data)
        
        # Third sub-operation
        with tracer.start_as_current_span("save_result"):
            await save_result(result)
        
        parent_span.set_attribute("items_processed", len(result))
        return result
```

### Error Handling

```python
async def risky_operation():
    with tracer.start_as_current_span("risky_operation") as span:
        try:
            result = await do_something_risky()
            span.set_attribute("success", True)
            return result
        except Exception as e:
            span.set_attribute("success", False)
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            span.record_exception(e)  # Records full exception details
            raise
```

## Common Span Attributes

### Resource Identifiers
```python
span.set_attribute("user.id", user_id)
span.set_attribute("photo.id", photo_id)
span.set_attribute("album.id", album_id)
```

### Operation Details
```python
span.set_attribute("operation.type", "image_generation")
span.set_attribute("operation.name", "generate_from_text")
span.set_attribute("operation.duration_ms", duration)
```

### Data Metrics
```python
span.set_attribute("data.size_bytes", len(data))
span.set_attribute("items.count", len(items))
span.set_attribute("batch.size", batch_size)
```

### Status
```python
span.set_attribute("success", True)
span.set_attribute("status", "completed")
span.set_attribute("error.message", error_msg)
```

## Automatic Instrumentation

These are automatically traced (no code changes needed):

✅ **All FastAPI routes**
- HTTP method, path, status code
- Request/response headers
- Query parameters

✅ **All database queries**
- SQL statements
- Query duration
- Database name

✅ **All HTTP client requests**
- URL, method, status code
- Request/response details

## Disable Tracing

### Globally
```bash
# In .env file
ENABLE_TRACING=false
```

### For Specific Operations
```python
from opentelemetry import trace

# Suppress tracing for a specific operation
with trace.use_span(trace.INVALID_SPAN):
    # This code won't be traced
    result = await untraced_operation()
```

## Best Practices

### ✅ DO

- Add spans for business-critical operations
- Include meaningful attributes (user_id, resource_id, etc.)
- Record exceptions in spans
- Use descriptive span names
- Add metrics (size, count, duration)

### ❌ DON'T

- Add spans for every tiny operation (creates noise)
- Include sensitive data in attributes (passwords, tokens)
- Forget to handle exceptions in spans
- Use generic span names like "function" or "operation"
- Add too many attributes (keep it relevant)

## Troubleshooting

### Traces Not Appearing

```bash
# Check if tracing is enabled
grep ENABLE_TRACING .env

# Check Cloud Trace API is enabled
gcloud services list --enabled | grep cloudtrace

# Check IAM permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/cloudtrace.agent"
```

### High Latency

```python
# Implement sampling (in configs/tracing.py)
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
sampler = TraceIdRatioBased(0.1)
tracer_provider = TracerProvider(sampler=sampler, resource=resource)
```

## Examples

See `examples/tracing_example.py` for a complete working example.

## Resources

- [Full Documentation](TRACING.md)
- [Cloud Trace Console](https://console.cloud.google.com/traces)
- [OpenTelemetry Docs](https://opentelemetry.io/docs/instrumentation/python/)

