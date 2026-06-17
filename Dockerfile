# ──────────────────────────────────────────────
# Stage 1: Dependency resolution with uv
# ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency manifests first (layer cache optimization)
COPY pyproject.toml uv.lock ./

# Install production dependencies into /app/.venv
RUN uv sync --no-dev --frozen

# ──────────────────────────────────────────────
# Stage 2: Final runtime image
# ──────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy uv binary and the pre-built virtual environment
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY src/ ./src/

# Ensure the venv's executables take precedence
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Default: run the webhook server
CMD ["python", "-m", "src.presentation.cli", "serve"]
