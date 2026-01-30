# Backend Dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev && \
    uv run playwright install --with-deps chromium

# Copy application code
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Expose port (can be overridden by PORT env var)
EXPOSE 8000

# Default port, can be overridden by environment variable
ENV PORT=8000

# Run the application
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]