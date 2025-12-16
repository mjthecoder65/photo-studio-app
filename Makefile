.PHONY: help install test lint format clean run docker-build docker-run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	poetry install

install-dev: ## Install development dependencies
	poetry install --with dev

update: ## Update dependencies
	poetry update

test: ## Run all tests
	poetry run pytest -v

test-unit: ## Run unit tests only
	poetry run pytest tests/unit -v -m "not integration"

test-integration: ## Run integration tests only
	poetry run pytest tests/integration -v -m "not unit"

test-cov: ## Run tests with coverage
	poetry run pytest --cov=. --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	poetry run ruff check .

lint-fix: ## Run linting checks and fix issues
	poetry run ruff check --fix .

format: ## Format code
	poetry run ruff format .

format-check: ## Check code formatting
	poetry run ruff format --check .

security: ## Run security checks
	poetry run bandit -r . -f screen

pre-commit: ## Run pre-commit hooks
	poetry run pre-commit run --all-files

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov coverage.xml .coverage

run: ## Run the application locally
	poetry run python main.py

run-dev: ## Run the application in development mode
	poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8080

docker-build: ## Build Docker image
	docker build -t photo-studio-app:latest .

docker-run: ## Run Docker container
	docker run -p 8080:8080 --env-file .env photo-studio-app:latest

docker-compose-up: ## Start services with docker-compose
	docker-compose up -d

docker-compose-down: ## Stop services with docker-compose
	docker-compose down

db-migrate: ## Run database migrations
	poetry run alembic upgrade head

db-rollback: ## Rollback last database migration
	poetry run alembic downgrade -1

db-revision: ## Create a new database migration
	@read -p "Enter migration message: " msg; \
	poetry run alembic revision --autogenerate -m "$$msg"

ci: lint format-check test ## Run CI checks locally

all: install lint format test ## Install, lint, format, and test

