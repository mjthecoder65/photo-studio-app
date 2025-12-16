# Tests

This directory contains tests for the Demo-App Service.

## Test Structure

- `unit/` - Unit tests that test individual functions and components in isolation
- `integration/` - Integration tests that test the API endpoints with the full application

## Setup

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

Or with poetry:

```bash
poetry add --group dev pytest pytest-asyncio pytest-cov httpx
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run only unit tests

```bash
pytest tests/unit/
```

### Run only integration tests

```bash
pytest tests/integration/
```

### Run tests with coverage

```bash
pytest --cov=. --cov-report=html
```

### Run specific test file

```bash
pytest tests/integration/test_healthy.py
```

### Run specific test class or function

```bash
pytest tests/integration/test_healthy.py::TestHealthyEndpoint::test_healthy_endpoint_returns_200
```

### Run tests with coverage report

```bash
pytest tests/ --cov=routers.healthy --cov-report=term-missing
```

## Test Coverage

The tests cover:

### Healthy Endpoint (`/healthy`)

**Integration Tests:**

- Returns 200 status code
- Returns correct JSON structure (status, app, version)
- Returns correct values for each field
- Returns correct content type
- Handles trailing slashes
- Responds quickly (performance test)
- Handles multiple consecutive requests
- Rejects unsupported HTTP methods (POST, PUT, DELETE, PATCH)

**Unit Tests:**

- Function returns correct dictionary structure
- Function uses settings correctly
- Function returns correct data types
- Function works with different configuration values
