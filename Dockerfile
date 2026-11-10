# syntax=docker/dockerfile:1
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/packages/core:/app/packages/providers:/app/packages/analyzers:/app/packages/scoring:/app/packages/reporting:/app/packages/ai:/app/apps/api:/app/apps/cli

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject and install dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir ".[ai]"

# Copy project source packages and applications
COPY packages/ ./packages/
COPY apps/api/ ./apps/api/
COPY apps/cli/ ./apps/cli/

# Install package in editable/local mode
RUN pip install --no-cache-dir -e . --no-deps

# Create runtime data directory
RUN mkdir -p /app/data && chmod 777 /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "libscope.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
