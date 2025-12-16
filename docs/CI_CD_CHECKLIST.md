# CI/CD Setup Checklist

Use this checklist to set up CI/CD for the Photo Studio application.

## Prerequisites

- [ ] GitHub repository created
- [ ] Admin access to GitHub repository
- [ ] Google Cloud Platform project created
- [ ] `gcloud` CLI installed and configured
- [ ] Repository cloned locally

## Local Setup

### 1. Install Dependencies

- [ ] Install Poetry
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```

- [ ] Install project dependencies
  ```bash
  make install-dev
  ```

- [ ] Verify tools are installed
  ```bash
  poetry run ruff --version
  poetry run pytest --version
  poetry run bandit --version
  ```

### 2. Configure Pre-commit Hooks (Optional)

- [ ] Install pre-commit hooks
  ```bash
  poetry run pre-commit install
  ```

- [ ] Test pre-commit hooks
  ```bash
  poetry run pre-commit run --all-files
  ```

### 3. Test Locally

- [ ] Run linting
  ```bash
  make lint
  ```

- [ ] Run formatting
  ```bash
  make format
  ```

- [ ] Run tests
  ```bash
  make test
  ```

- [ ] Run all CI checks
  ```bash
  make ci
  ```

## Google Cloud Setup

### 1. Enable Required APIs

- [ ] Enable Cloud Run API
  ```bash
  gcloud services enable run.googleapis.com --project=YOUR_PROJECT_ID
  ```

- [ ] Enable Artifact Registry API
  ```bash
  gcloud services enable artifactregistry.googleapis.com --project=YOUR_PROJECT_ID
  ```

- [ ] Enable Secret Manager API
  ```bash
  gcloud services enable secretmanager.googleapis.com --project=YOUR_PROJECT_ID
  ```

- [ ] Enable Cloud Trace API
  ```bash
  gcloud services enable cloudtrace.googleapis.com --project=YOUR_PROJECT_ID
  ```

### 2. Create Artifact Registry Repository

- [ ] Create Docker repository
  ```bash
  gcloud artifacts repositories create photo-studio \
    --repository-format=docker \
    --location=us-central1 \
    --description="Photo Studio Docker images" \
    --project=YOUR_PROJECT_ID
  ```

### 3. Set Up Workload Identity Federation

Follow the detailed guide in `docs/GITHUB_ACTIONS_SETUP.md`

- [ ] Create Workload Identity Pool
- [ ] Create Workload Identity Provider
- [ ] Create GitHub Actions service account
- [ ] Grant necessary IAM roles
- [ ] Allow GitHub to impersonate service account
- [ ] Get provider resource name

### 4. Create Cloud Run Service Account

- [ ] Create service account
  ```bash
  gcloud iam service-accounts create photo-studio-run \
    --project=YOUR_PROJECT_ID \
    --display-name="Photo Studio Cloud Run Service Account"
  ```

- [ ] Grant necessary roles
  - `roles/cloudsql.client`
  - `roles/storage.objectViewer`
  - `roles/secretmanager.secretAccessor`
  - `roles/cloudtrace.agent`

### 5. Store Secrets in Secret Manager

- [ ] Create `DATABASE_URL` secret
- [ ] Create `JWT_SECRET_KEY` secret
- [ ] Create `GEMINI_API_KEY` secret
- [ ] Grant access to Cloud Run service account

## GitHub Setup

### 1. Enable GitHub Actions

- [ ] Go to Settings → Actions → General
- [ ] Enable "Allow all actions and reusable workflows"
- [ ] Save settings

### 2. Configure Repository Secrets

Navigate to Settings → Secrets and variables → Actions

- [ ] Add `GCP_PROJECT_ID`
- [ ] Add `WIF_PROVIDER`
- [ ] Add `WIF_SERVICE_ACCOUNT`
- [ ] Add `CLOUD_RUN_SERVICE_ACCOUNT`
- [ ] Add `CODECOV_TOKEN` (optional)

### 3. Configure Branch Protection

- [ ] Go to Settings → Branches
- [ ] Add rule for `main` branch
- [ ] Enable "Require pull request reviews before merging"
- [ ] Enable "Require status checks to pass before merging"
  - [ ] Select `lint` check
  - [ ] Select `test` check
  - [ ] Select `security` check
  - [ ] Select `build` check
- [ ] Enable "Require branches to be up to date before merging"
- [ ] Save changes

### 4. Configure Environments (Optional)

- [ ] Go to Settings → Environments
- [ ] Create `production` environment
- [ ] Create `staging` environment
- [ ] Add environment-specific secrets if needed

## Testing the Setup

### 1. Test CI Workflow

- [ ] Create a new branch
  ```bash
  git checkout -b test-ci
  ```

- [ ] Make a small change
  ```bash
  echo "# Test" >> README.md
  git add README.md
  git commit -m "Test CI workflow"
  ```

- [ ] Push to GitHub
  ```bash
  git push origin test-ci
  ```

- [ ] Create pull request
- [ ] Verify all CI checks pass
  - [ ] Lint job passes
  - [ ] Test job passes
  - [ ] Security job passes
  - [ ] Build job passes

### 2. Test Deploy Workflow

- [ ] Merge test PR to main
- [ ] Check that deploy workflow runs
- [ ] Verify deployment in Cloud Run console
- [ ] Test deployed application
  ```bash
  curl https://YOUR_SERVICE_URL/api/v1/healthy
  ```

### 3. Test Manual Deployment

- [ ] Go to Actions → Deploy to Cloud Run
- [ ] Click "Run workflow"
- [ ] Select environment (staging/production)
- [ ] Run workflow
- [ ] Verify deployment succeeds

## Codecov Setup (Optional)

- [ ] Sign up at https://codecov.io
- [ ] Add repository
- [ ] Copy upload token
- [ ] Add `CODECOV_TOKEN` to GitHub secrets
- [ ] Verify coverage reports appear after CI runs

## Documentation

- [ ] Update README.md with your repository URL
- [ ] Update workflow files with your project details
- [ ] Document any custom configuration
- [ ] Share setup guide with team

## Verification

### Final Checks

- [ ] All CI workflows pass on main branch
- [ ] Deployment workflow successfully deploys to Cloud Run
- [ ] Application is accessible and healthy
- [ ] Traces appear in Cloud Trace
- [ ] Secrets are properly configured
- [ ] Branch protection is enabled
- [ ] Team members have appropriate access

### Smoke Tests

- [ ] Health endpoint works
  ```bash
  curl https://YOUR_SERVICE_URL/api/v1/healthy
  ```

- [ ] API documentation is accessible
  ```bash
  curl https://YOUR_SERVICE_URL/docs
  ```

- [ ] Authentication works (if applicable)

## Troubleshooting

If something doesn't work:

1. **Check workflow logs** in GitHub Actions
2. **Review documentation** in `docs/CI_CD.md`
3. **Test locally** with `make ci`
4. **Verify secrets** are correctly configured
5. **Check IAM permissions** in Google Cloud
6. **Review service account** permissions

## Next Steps

After successful setup:

- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up error tracking (e.g., Sentry)
- [ ] Create runbooks for common issues
- [ ] Schedule regular dependency updates
- [ ] Set up performance monitoring

## Resources

- [CI/CD Documentation](CI_CD.md)
- [GitHub Actions Setup Guide](GITHUB_ACTIONS_SETUP.md)
- [Tracing Documentation](TRACING.md)
- [Makefile](../Makefile) - All available commands

## Success Criteria

✅ CI workflow runs on every PR
✅ All tests pass before merge
✅ Code is automatically linted and formatted
✅ Security scans run on every PR
✅ Deployment happens automatically on merge to main
✅ Application is accessible after deployment
✅ Traces appear in Cloud Trace
✅ Team can develop and deploy confidently

