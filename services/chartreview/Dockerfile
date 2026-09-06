# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/workspace/.venv/bin:$PATH"
WORKDIR /workspace

FROM base AS dependencies

COPY pyproject.toml uv.lock ./
COPY packages/folium-core/pyproject.toml packages/folium-core/pyproject.toml
COPY services/chartreview/pyproject.toml services/chartreview/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --frozen --no-dev --no-install-workspace --package chartreview

FROM dependencies

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --frozen --no-dev --package chartreview
WORKDIR /workspace/services/chartreview
CMD ["uv", "run", "--frozen", "--no-sync", "--package", "chartreview", "python", "-m", "app.worker"]