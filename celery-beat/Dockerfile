# Celery Beat Dockerfile
# Must be placed at repo root level to access backend/ folder
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project files from backend directory
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code from backend directory
COPY backend/src ./src
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./

# Run the celery beat scheduler
CMD ["uv", "run", "celery", "-A", "src.worker:celery_app", "beat", "--loglevel=info"]
