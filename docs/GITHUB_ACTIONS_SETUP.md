# GitHub Actions Setup Guide

This guide walks you through setting up GitHub Actions CI/CD for the Photo Studio application.

## Prerequisites

- GitHub repository with admin access
- Google Cloud Platform project
- Service account with appropriate permissions

## Step 1: Enable GitHub Actions

GitHub Actions is enabled by default for public repositories. For private repositories:

1. Go to repository **Settings** → **Actions** → **General**
2. Under "Actions permissions", select **Allow all actions and reusable workflows**
3. Click **Save**

## Step 2: Configure Repository Secrets

### Navigate to Secrets

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

### Add Required Secrets

#### For CI Workflow (Optional)

| Secret Name | Description | Example |
|------------|-------------|---------|
| `CODECOV_TOKEN` | Codecov upload token | `abc123...` |

#### For Deploy Workflow (Required)

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `GCP_PROJECT_ID` | Google Cloud project ID | From GCP Console |
| `WIF_PROVIDER` | Workload Identity Federation provider | See Step 3 |
| `WIF_SERVICE_ACCOUNT` | Service account email | See Step 3 |
| `CLOUD_RUN_SERVICE_ACCOUNT` | Cloud Run service account | See Step 4 |

## Step 3: Set Up Workload Identity Federation

Workload Identity Federation allows GitHub Actions to authenticate to Google Cloud without storing service account keys.

### Create Workload Identity Pool

```bash
export PROJECT_ID="your-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export GITHUB_REPO="YOUR_ORG/photo-studio"

# Create pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

### Create Workload Identity Provider

```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --project="${PROJECT_ID}" \
  --display-name="GitHub Actions Service Account"

export SA_EMAIL="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"
```

### Grant Permissions

```bash
# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"
```

### Allow GitHub to Impersonate Service Account

```bash
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"
```

### Get Provider Resource Name

```bash
gcloud iam workload-identity-pools providers describe "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

Copy the output and add it as `WIF_PROVIDER` secret in GitHub.

Example: `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

Add the service account email as `WIF_SERVICE_ACCOUNT` secret:
```
github-actions@your-project-id.iam.gserviceaccount.com
```

## Step 4: Create Cloud Run Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create photo-studio-run \
  --project="${PROJECT_ID}" \
  --display-name="Photo Studio Cloud Run Service Account"

export RUN_SA_EMAIL="photo-studio-run@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${RUN_SA_EMAIL}" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${RUN_SA_EMAIL}" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${RUN_SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${RUN_SA_EMAIL}" \
  --role="roles/cloudtrace.agent"
```

Add the service account email as `CLOUD_RUN_SERVICE_ACCOUNT` secret in GitHub.

## Step 5: Create Artifact Registry Repository

```bash
# Create repository for Docker images
gcloud artifacts repositories create photo-studio \
  --repository-format=docker \
  --location=us-central1 \
  --description="Photo Studio Docker images" \
  --project="${PROJECT_ID}"
```

## Step 6: Store Secrets in Secret Manager

```bash
# Create secrets
echo -n "your-database-url" | gcloud secrets create DATABASE_URL \
  --data-file=- \
  --project="${PROJECT_ID}"

echo -n "your-jwt-secret" | gcloud secrets create JWT_SECRET_KEY \
  --data-file=- \
  --project="${PROJECT_ID}"

echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- \
  --project="${PROJECT_ID}"

# Grant access to Cloud Run service account
for SECRET in DATABASE_URL JWT_SECRET_KEY GEMINI_API_KEY; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${RUN_SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="${PROJECT_ID}"
done
```

## Step 7: Update Workflow Files

Update the workflow files with your specific values:

### `.github/workflows/deploy.yml`

```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  SERVICE_NAME: photo-studio-app
  REGION: us-central1  # Change if needed
```

## Step 8: Test the Setup

### Test CI Workflow

1. Create a new branch
2. Make a small change
3. Push to GitHub
4. Create a pull request
5. Check that CI workflow runs successfully

### Test Deploy Workflow

1. Merge PR to main branch
2. Check that deploy workflow runs
3. Verify deployment in Cloud Run console
4. Test the deployed application

## Troubleshooting

### Workflow Permission Errors

If you see permission errors:

```bash
# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:${SA_EMAIL}"
```

### Workload Identity Issues

```bash
# Verify Workload Identity binding
gcloud iam service-accounts get-iam-policy ${SA_EMAIL} \
  --project="${PROJECT_ID}"
```

### Secret Access Issues

```bash
# Check secret permissions
gcloud secrets get-iam-policy DATABASE_URL --project="${PROJECT_ID}"
```

## Security Best Practices

1. **Use Workload Identity Federation** instead of service account keys
2. **Limit permissions** to only what's needed (principle of least privilege)
3. **Rotate secrets** regularly
4. **Enable branch protection** for main branch
5. **Require PR reviews** before merging
6. **Enable security scanning** (Dependabot, CodeQL)

## Next Steps

1. Set up branch protection rules
2. Configure Codecov for coverage reporting
3. Add status checks to PRs
4. Set up deployment environments (staging, production)
5. Configure notifications for workflow failures

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)

