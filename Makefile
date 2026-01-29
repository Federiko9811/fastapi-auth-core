.PHONY: help install dev test lint format migrate run clean

# Default target
help:
	@echo "FastAPI Auth Core - Available commands:"
	@echo ""
	@echo "  make install     Install production dependencies"
	@echo "  make dev         Install dev dependencies and pre-commit hooks"
	@echo "  make test        Run tests"
	@echo "  make lint        Run linter (ruff check)"
	@echo "  make format      Format code (ruff format)"
	@echo "  make migrate     Run database migrations"
	@echo "  make run         Start development server"
	@echo "  make clean       Remove cache files"
	@echo ""

# Install production dependencies
install:
	uv sync

# Install dev dependencies and set up pre-commit
dev:
	uv sync --dev
	uv run pre-commit install

# Run tests
test:
	POSTGRES_SERVER=localhost uv run pytest tests/ -v

# Run linter
lint:
	uv run ruff check app/ tests/

# Format code
format:
	uv run ruff format app/ tests/
	uv run ruff check --fix app/ tests/

# Run database migrations
migrate:
	POSTGRES_SERVER=localhost uv run alembic upgrade head

# Create new migration (usage: make migration msg="Add new table")
migration:
	POSTGRES_SERVER=localhost uv run alembic revision --autogenerate -m "$(msg)"

# Start development server
run:
	POSTGRES_SERVER=localhost uv run uvicorn app.main:app --reload

# Start database only (Docker)
db:
	docker-compose up -d db

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
