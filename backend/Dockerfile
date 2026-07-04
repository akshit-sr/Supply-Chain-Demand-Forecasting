# Backend: FastAPI + ML, managed by uv
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# System deps for lightgbm
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 && rm -rf /var/lib/apt/lists/*

# Install dependencies first (cached layer). The CPU torch wheel is used inside the
# container (the Intel XPU runtime is host-specific); the trained model is portable.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# App code, data, and pre-trained artifacts
COPY app ./app
COPY data ./data
COPY artifacts ./artifacts

# Install the project itself into the environment.
RUN uv sync --frozen

EXPOSE 8000
CMD ["uv", "run", "--frozen", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
