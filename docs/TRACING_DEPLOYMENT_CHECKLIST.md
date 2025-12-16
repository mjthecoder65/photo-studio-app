# Tracing Deployment Checklist

Use this checklist when deploying the application with Google Cloud Trace enabled.

## Pre-Deployment

### 1. Google Cloud Setup

- [ ] **Enable Cloud Trace API**
  ```bash
  gcloud services enable cloudtrace.googleapis.com --project=YOUR_PROJECT_ID
  ```

- [ ] **Verify API is enabled**
  ```bash
  gcloud services list --enabled --project=YOUR_PROJECT_ID | grep cloudtrace
  ```

### 2. IAM Permissions

- [ ] **Grant Cloud Trace Agent role to service account**
  ```bash
  gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudtrace.agent"
  ```

- [ ] **Verify permissions**
  ```bash
  gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.role:roles/cloudtrace.agent"
  ```

### 3. Environment Configuration

- [ ] **Set environment variables**
  ```bash
  # In .env or deployment config
  ENABLE_TRACING=true
  GCS_PROJECT_ID=your-project-id
  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json  # If not using default credentials
  ```

- [ ] **Verify settings**
  ```bash
  poetry run python -c "from configs.settings import settings; print(f'Tracing: {settings.ENABLE_TRACING}, Project: {settings.GCS_PROJECT_ID}')"
  ```

### 4. Dependencies

- [ ] **Verify OpenTelemetry packages are installed**
  ```bash
  poetry show | grep opentelemetry
  ```

- [ ] **Expected packages:**
  - opentelemetry-api
  - opentelemetry-sdk
  - opentelemetry-instrumentation-fastapi
  - opentelemetry-instrumentation-sqlalchemy
  - opentelemetry-instrumentation-httpx
  - opentelemetry-exporter-gcp-trace

## Deployment

### 5. Local Testing

- [ ] **Test tracing setup locally**
  ```bash
  poetry run python main.py
  ```

- [ ] **Verify startup message**
  ```
  ✅ Tracing enabled - exporting to Google Cloud Trace (Project: your-project-id)
  ```

- [ ] **Make a test request**
  ```bash
  curl http://localhost:8080/api/v1/healthy
  ```

- [ ] **Check Cloud Trace console for traces**
  - Go to: https://console.cloud.google.com/traces/list
  - Filter by service: `photo-studio-app`
  - Verify traces appear (may take 30-60 seconds)

### 6. Cloud Run Deployment (if applicable)

- [ ] **Update Cloud Run service with environment variables**
  ```bash
  gcloud run deploy photo-studio-app \
    --set-env-vars ENABLE_TRACING=true \
    --set-env-vars GCS_PROJECT_ID=YOUR_PROJECT_ID \
    --service-account YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --region YOUR_REGION
  ```

- [ ] **Verify service account has Cloud Trace Agent role**

- [ ] **Test deployed service**
  ```bash
  curl https://YOUR_SERVICE_URL/api/v1/healthy
  ```

### 7. Kubernetes Deployment (if applicable)

- [ ] **Add environment variables to deployment manifest**
  ```yaml
  env:
    - name: ENABLE_TRACING
      value: "true"
    - name: GCS_PROJECT_ID
      value: "your-project-id"
  ```

- [ ] **Ensure Workload Identity is configured** (recommended)
  - Or mount service account key as secret

- [ ] **Apply deployment**
  ```bash
  kubectl apply -f deployment.yaml
  ```

## Post-Deployment

### 8. Verification

- [ ] **Check application logs for tracing initialization**
  ```bash
  # Cloud Run
  gcloud run services logs read photo-studio-app --region YOUR_REGION --limit 50

  # Kubernetes
  kubectl logs -l app=photo-studio-app --tail=50
  ```

- [ ] **Verify traces in Cloud Console**
  - Navigate to Cloud Trace
  - Filter by service: `photo-studio-app`
  - Check recent traces appear

- [ ] **Test critical endpoints**
  - [ ] Health check: `/api/v1/healthy`
  - [ ] AI image generation: `/api/v1/ai-photos/generate`
  - [ ] Photo upload: `/api/v1/photos`

- [ ] **Verify trace attributes**
  - Click on a trace
  - Check for custom attributes (e.g., `ai.model`, `user.id`)
  - Verify nested spans appear correctly

### 9. Monitoring Setup

- [ ] **Create Cloud Monitoring dashboard** (optional)
  - Add latency charts
  - Add error rate charts
  - Add request count charts

- [ ] **Set up alerts** (optional)
  ```bash
  # Example: Alert on high latency
  gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Latency Alert" \
    --condition-display-name="Latency > 5s" \
    --condition-threshold-value=5000 \
    --condition-threshold-duration=60s
  ```

### 10. Performance Validation

- [ ] **Check trace overhead**
  - Compare response times with/without tracing
  - Ensure overhead is acceptable (typically <5%)

- [ ] **Monitor trace volume**
  - Check number of traces per minute
  - Consider implementing sampling if volume is high

- [ ] **Verify batch export is working**
  - Traces should appear in batches
  - No significant delay in trace visibility

## Troubleshooting

### If traces don't appear:

1. **Check application logs**
   ```bash
   # Look for tracing initialization message
   grep "Tracing enabled" logs.txt
   ```

2. **Verify API is enabled**
   ```bash
   gcloud services list --enabled | grep cloudtrace
   ```

3. **Check IAM permissions**
   ```bash
   gcloud projects get-iam-policy YOUR_PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:YOUR_SERVICE_ACCOUNT"
   ```

4. **Test with tracing disabled**
   ```bash
   # Set ENABLE_TRACING=false and verify app still works
   ```

5. **Check for errors in logs**
   ```bash
   # Look for OpenTelemetry errors
   grep -i "opentelemetry\|trace\|span" logs.txt
   ```

## Rollback Plan

If tracing causes issues:

- [ ] **Disable tracing immediately**
  ```bash
  # Set environment variable
  ENABLE_TRACING=false
  
  # Redeploy
  gcloud run deploy photo-studio-app --set-env-vars ENABLE_TRACING=false
  ```

- [ ] **Application continues to work** (tracing is non-blocking)

- [ ] **Investigate issues** in logs

- [ ] **Re-enable after fixing**

## Success Criteria

✅ Application starts successfully with tracing enabled
✅ Traces appear in Cloud Trace console within 60 seconds
✅ Custom spans and attributes are visible
✅ No significant performance degradation (<5% overhead)
✅ No errors in application logs related to tracing

## Resources

- [Full Documentation](TRACING.md)
- [Quick Reference](TRACING_QUICK_REFERENCE.md)
- [Setup Summary](../TRACING_SETUP_SUMMARY.md)
- [Cloud Trace Console](https://console.cloud.google.com/traces)

