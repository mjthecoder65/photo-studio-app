# CI/CD Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) setup for the Photo Studio application.

## Overview

The project uses GitHub Actions for automated testing, security scanning, and deployment to Google Cloud Run.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and pull request to `main` and `develop` branches.

#### Jobs

**Lint**
- Checks code formatting with Ruff
- Runs linting checks with Ruff
- Ensures code quality standards

**Test**
- Runs unit tests
- Runs integration tests with PostgreSQL
- Generates coverage reports
- Uploads coverage to Codecov
- Tests against Python 3.13

**Security**
- Runs Bandit security scanner
- Checks for known vulnerabilities with Safety
- Uploads security reports as artifacts

**Build**
- Builds Docker image
- Tests Docker image functionality
- Uses Docker layer caching for faster builds

### 2. Deploy Workflow (`.github/workflows/deploy.yml`)

Deploys the application to Google Cloud Run.

#### Triggers
- Automatic deployment on push to `main` branch
- Manual deployment via workflow dispatch

#### Steps
1. Authenticates to Google Cloud using Workload Identity
2. Builds and pushes Docker image to Artifact Registry
3. Deploys to Cloud Run with environment variables and secrets
4. Runs smoke tests against deployed service
5. Creates deployment summary

### 3. Dependency Review (`.github/workflows/dependency-review.yml`)

Reviews dependencies in pull requests for security vulnerabilities.

## Local Development

### Prerequisites

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
make install-dev

# Install pre-commit hooks (optional)
poetry run pre-commit install
```

### Common Commands

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Lint code
make lint

# Format code
make format

# Run security checks
make security

# Run all CI checks locally
make ci

# Run the application
make run-dev
```

### Pre-commit Hooks

Pre-commit hooks automatically run checks before each commit:

```bash
# Install hooks
poetry run pre-commit install

# Run manually
make pre-commit
```

Hooks include:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Large file detection
- Private key detection
- Ruff linting and formatting
- Bandit security scanning

## GitHub Secrets Configuration

### Required Secrets

#### For CI Workflow

- `CODECOV_TOKEN` (optional) - Codecov upload token

#### For Deploy Workflow

- `GCP_PROJECT_ID` - Google Cloud project ID
- `WIF_PROVIDER` - Workload Identity Federation provider
- `WIF_SERVICE_ACCOUNT` - Service account for Workload Identity
- `CLOUD_RUN_SERVICE_ACCOUNT` - Service account for Cloud Run

#### Secret Manager Secrets (in GCP)

These are referenced in the deploy workflow:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - JWT signing key
- `GEMINI_API_KEY` - Google Gemini API key

### Setting Up Workload Identity Federation

```bash
# Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Grant permissions to service account
gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT_EMAIL}" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"
```

## CI/CD Pipeline Flow

### Pull Request Flow

```
1. Developer creates PR
   ↓
2. CI workflow runs
   ├── Lint check
   ├── Tests (unit + integration)
   ├── Security scan
   └── Docker build
   ↓
3. Dependency review
   ↓
4. Code review
   ↓
5. Merge to main
```

### Deployment Flow

```
1. Merge to main
   ↓
2. CI workflow runs (validation)
   ↓
3. Deploy workflow triggers
   ├── Build Docker image
   ├── Push to Artifact Registry
   ├── Deploy to Cloud Run
   └── Run smoke tests
   ↓
4. Deployment complete
```

## Monitoring and Debugging

### View Workflow Runs

```
https://github.com/YOUR_ORG/YOUR_REPO/actions
```

### Download Artifacts

Security reports and test results are uploaded as artifacts and can be downloaded from the workflow run page.

### Check Deployment Status

```bash
# Get Cloud Run service status
gcloud run services describe photo-studio-app --region us-central1

# View logs
gcloud run services logs read photo-studio-app --region us-central1
```

## Best Practices

### Code Quality

1. **Always run tests locally** before pushing
   ```bash
   make test
   ```

2. **Format code** before committing
   ```bash
   make format
   ```

3. **Run linting** to catch issues early
   ```bash
   make lint
   ```

4. **Check security** for vulnerabilities
   ```bash
   make security
   ```

### Pull Requests

1. Keep PRs small and focused
2. Ensure all CI checks pass
3. Add tests for new features
4. Update documentation as needed
5. Request reviews from team members

### Deployment

1. Test thoroughly in staging before production
2. Monitor logs after deployment
3. Run smoke tests to verify deployment
4. Have a rollback plan ready

## Troubleshooting

### CI Failures

**Lint failures**
```bash
# Fix automatically
make lint-fix
make format
```

**Test failures**
```bash
# Run tests locally with verbose output
poetry run pytest -vv

# Run specific test
poetry run pytest tests/path/to/test.py::test_name -vv
```

**Security scan failures**
```bash
# Review Bandit report
poetry run bandit -r . -f screen

# Check Safety report
poetry run safety check
```

### Deployment Failures

**Authentication issues**
- Verify Workload Identity Federation setup
- Check service account permissions

**Image build failures**
- Check Dockerfile syntax
- Verify all dependencies are in pyproject.toml

**Cloud Run deployment failures**
- Check service account has necessary roles
- Verify secrets exist in Secret Manager
- Check resource limits (memory, CPU)

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Poetry Documentation](https://python-poetry.org/docs/)

