# CI/CD Quick Start Guide

Get your CI/CD pipeline up and running in 15 minutes.

## Prerequisites

- GitHub repository with admin access
- Google Cloud project
- `gcloud` CLI installed

## Step 1: Local Setup (2 minutes)

```bash
# Install dependencies
make install-dev

# Test that everything works
make ci
```

## Step 2: Google Cloud Setup (5 minutes)

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export GITHUB_REPO="YOUR_ORG/photo-studio"

# Enable APIs
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudtrace.googleapis.com \
  --project=$PROJECT_ID

# Create Artifact Registry repository
gcloud artifacts repositories create photo-studio \
  --repository-format=docker \
  --location=us-central1 \
  --project=$PROJECT_ID
```

## Step 3: Workload Identity Federation (5 minutes)

```bash
# Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --project=$PROJECT_ID \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create service account
gcloud iam service-accounts create github-actions \
  --project=$PROJECT_ID \
  --display-name="GitHub Actions"

export SA_EMAIL="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant permissions
for ROLE in roles/run.admin roles/storage.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE"
done

# Allow GitHub to impersonate
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"

# Get provider name (save this for GitHub secrets)
gcloud iam workload-identity-pools providers describe "github-provider" \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

## Step 4: Create Secrets (2 minutes)

```bash
# Create secrets in Secret Manager
echo -n "your-database-url" | gcloud secrets create DATABASE_URL --data-file=- --project=$PROJECT_ID
echo -n "your-jwt-secret" | gcloud secrets create JWT_SECRET_KEY --data-file=- --project=$PROJECT_ID
echo -n "your-gemini-key" | gcloud secrets create GEMINI_API_KEY --data-file=- --project=$PROJECT_ID

# Create Cloud Run service account
gcloud iam service-accounts create photo-studio-run \
  --project=$PROJECT_ID \
  --display-name="Photo Studio Cloud Run"

export RUN_SA_EMAIL="photo-studio-run@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant permissions
for ROLE in roles/cloudsql.client roles/storage.objectViewer roles/secretmanager.secretAccessor roles/cloudtrace.agent; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${RUN_SA_EMAIL}" \
    --role="$ROLE"
done

# Grant secret access
for SECRET in DATABASE_URL JWT_SECRET_KEY GEMINI_API_KEY; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${RUN_SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID
done
```

## Step 5: Configure GitHub Secrets (1 minute)

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value |
|------------|-------|
| `GCP_PROJECT_ID` | Your project ID |
| `WIF_PROVIDER` | Output from Step 3 (provider name) |
| `WIF_SERVICE_ACCOUNT` | `github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com` |
| `CLOUD_RUN_SERVICE_ACCOUNT` | `photo-studio-run@YOUR_PROJECT_ID.iam.gserviceaccount.com` |

## Step 6: Test It! (2 minutes)

```bash
# Create a test branch
git checkout -b test-ci

# Make a change
echo "# CI/CD Test" >> README.md
git add README.md
git commit -m "Test CI/CD pipeline"

# Push and create PR
git push origin test-ci
```

Go to GitHub and create a pull request. You should see:
- ✅ Lint check running
- ✅ Test check running
- ✅ Security check running
- ✅ Build check running

Merge the PR and watch the deployment happen automatically!

## Verify Deployment

```bash
# Get the service URL
gcloud run services describe photo-studio-app \
  --region us-central1 \
  --format="value(status.url)"

# Test the health endpoint
curl $(gcloud run services describe photo-studio-app --region us-central1 --format="value(status.url)")/api/v1/healthy
```

## Common Issues

### "Permission denied" errors
- Check that service accounts have the correct IAM roles
- Verify Workload Identity Federation is configured correctly

### "Secret not found" errors
- Ensure secrets exist in Secret Manager
- Verify Cloud Run service account has `secretmanager.secretAccessor` role

### Workflow doesn't trigger
- Check that GitHub Actions is enabled in repository settings
- Verify workflow files are in `.github/workflows/` directory

## Next Steps

1. **Set up branch protection** - Require CI checks before merge
2. **Configure environments** - Separate staging and production
3. **Add monitoring** - Set up alerts for failures
4. **Review documentation** - Read full docs in `docs/CI_CD.md`

## Full Documentation

- [Complete CI/CD Documentation](CI_CD.md)
- [Detailed Setup Guide](GITHUB_ACTIONS_SETUP.md)
- [Setup Checklist](CI_CD_CHECKLIST.md)

## Success!

If you've made it this far, you now have:
- ✅ Automated testing on every PR
- ✅ Code quality checks
- ✅ Security scanning
- ✅ Automatic deployment to Cloud Run
- ✅ No manual deployments needed!

Happy coding! 🚀

