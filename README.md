# Photo Studio App

[![Deploy](https://github.com/YOUR_ORG/photo-studio/actions/workflows/deploy.yml/badge.svg)](https://github.com/YOUR_ORG/photo-studio/actions/workflows/deploy.yml)

A modern photo management application with AI-powered image generation capabilities, built with FastAPI and deployed on Google Cloud Platform.

## Features

- 📸 **Photo Management** - Upload, organize, and manage photos
- 🎨 **AI Image Generation** - Generate images using Google Gemini AI
- 📁 **Album Organization** - Create and manage photo albums
- 🔐 **Authentication** - Secure JWT-based authentication
- 📊 **Distributed Tracing** - OpenTelemetry integration with Google Cloud Trace
- ☁️ **Cloud Storage** - Google Cloud Storage integration
- 🗄️ **Database** - PostgreSQL with async support

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.13
- **Database**: PostgreSQL (with asyncpg)
- **ORM**: SQLAlchemy 2.0
- **Cloud Platform**: Google Cloud Platform
  - Cloud Run
  - Cloud Storage
  - Cloud Firestore
  - Cloud Trace
  - Secret Manager
- **AI**: Google Gemini API
- **Authentication**: JWT (python-jose)
- **Testing**: pytest, pytest-asyncio
- **Linting**: Ruff
- **Security**: Bandit, Safety

## Quick Start

### Prerequisites

- Python 3.13+
- Poetry
- PostgreSQL
- Google Cloud Platform account

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_ORG/photo-studio.git
cd photo-studio

# Install dependencies
make install-dev

# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
vim .env

# Run database migrations
make db-migrate

# Start the application
make run-dev
```

The application will be available at `http://localhost:8080`

### Using Docker

```bash
# Build Docker image
make docker-build

# Run with Docker Compose
make docker-compose-up
```

## Development

### Common Commands

```bash
# Run tests
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
```

See the [Makefile](Makefile) for all available commands.

### Pre-commit Hooks

Install pre-commit hooks to automatically check code before committing:

```bash
poetry run pre-commit install
```

## Testing

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run with coverage report
make test-cov
```

## Documentation

- [CI/CD Documentation](docs/CI_CD.md) - Continuous Integration and Deployment
- [Tracing Documentation](docs/TRACING.md) - OpenTelemetry and Cloud Trace setup
- [Tracing Quick Reference](docs/TRACING_QUICK_REFERENCE.md) - Quick reference for tracing
- [Tracing Deployment Checklist](docs/TRACING_DEPLOYMENT_CHECKLIST.md) - Deployment checklist
- [AI Photo Generation](docs/AI_PHOTO_GENERATION.md) - AI image generation guide

## API Documentation

Once the application is running, visit:

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

## Deployment

The application is automatically deployed to Google Cloud Run on push to the `main` branch.

### Manual Deployment

```bash
# Deploy to production
gh workflow run deploy.yml

# Deploy to staging
gh workflow run deploy.yml -f environment=staging
```

See [CI/CD Documentation](docs/CI_CD.md) for detailed deployment instructions.

## Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Application
APP_NAME=photo-studio
APP_VERSION=v1
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Google Cloud
GCS_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-bucket-name
GEMINI_API_KEY=your-gemini-api-key

# Tracing
ENABLE_TRACING=true
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make ci`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.
