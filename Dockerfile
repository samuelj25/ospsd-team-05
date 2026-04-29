# Use a slim Python 3.11 image with `uv` pre-installed by Astral
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set working directory inside the container
WORKDIR /app

# Copy the project configuration files
COPY pyproject.toml uv.lock ./

# Copy the actual source code (uv needs workspace members to run sync)
COPY components/ ./components/

# Also copy README as it is referenced in pyproject.toml
COPY README.md ./

# Install git (required for uv to fetch GitHub dependencies)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install dependencies in frozen mode (strict lock file) and skip dev-dependencies
RUN uv sync --frozen --no-dev --all-packages

# Expose the standard FastAPI port
EXPOSE 8000

# Define the command to start the application using uvicorn (Render provides $PORT)
CMD ["sh", "-c", ".venv/bin/uvicorn calendar_client_service.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
