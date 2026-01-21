# Celery Beat Dockerfile
# Uses the same backend dependencies but runs celery beat instead of uvicorn
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project files from parent backend directory
COPY ../pyproject.toml ../uv.lock ../README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code from parent backend directory
COPY ../src ./src
COPY ../alembic ./alembic
COPY ../alembic.ini ./

# Run the celery beat scheduler
CMD ["uv", "run", "celery", "-A", "src.worker:celery_app", "beat", "--loglevel=info"]
