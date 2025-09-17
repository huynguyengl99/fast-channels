FROM ghcr.io/astral-sh/uv:python3.11-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies first (for better caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --all-extras

# Copy fast_channels package
COPY fast_channels/ fast_channels/

# Copy entire redis_sentinel test directory
COPY tests_extra/redis_sentinel/ .

# Set Python path so fast_channels can be imported
ENV PYTHONPATH=/app

# Set the default command to run pytest
CMD ["uv", "run", "pytest", "tests"]
