# Use Python 3.12 slim as base image
FROM python:3.12-slim

# 1. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Copy 'uv' from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. Create non-root user with home directory (-m flag)
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# 4. Set working directory
WORKDIR /app

# 5. Copy dependency configuration files
COPY pyproject.toml uv.lock ./

# 6. Install dependencies
# --frozen: use the lockfile exactly
# --no-cache: avoid writing cache during build
RUN uv sync --frozen --no-install-project --no-cache

# 7. Copy source code
COPY . .

# 8. Assign correct permissions
# Give user ownership of app directory and home (for uv cache at runtime)
RUN chown -R appuser:appuser /app /home/appuser

# 9. Switch to non-root user
USER appuser

# 10. Expose port
EXPOSE 8000

# 11. Set environment variables for uv
# UV_PYTHON_DOWNLOADS=never: prevent uv from downloading python at runtime
# UV_CACHE_DIR: force cache to a directory where we have permissions
ENV UV_PYTHON_DOWNLOADS=never \
    UV_CACHE_DIR=/home/appuser/.cache/uv

# 12. Start command - run migrations then start server
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
