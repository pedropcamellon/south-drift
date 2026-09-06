# syntax=docker/dockerfile:1.7
# Transcription service using the root uv workspace.
ARG PROVIDER=whisper
ARG WHISPER_MODEL_SIZE=base

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

WORKDIR /workspace

ENV PATH="/workspace/.venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

FROM base AS dependencies

ARG PROVIDER

COPY pyproject.toml uv.lock ./
COPY packages/folium-core/pyproject.toml packages/folium-core/pyproject.toml
COPY services/transcribe/pyproject.toml services/transcribe/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace --package transcribe --extra "${PROVIDER}"

FROM dependencies AS development

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package transcribe --extra "${PROVIDER}"

WORKDIR /workspace/services/transcribe

# Expose port
EXPOSE 8001

# Health check using wget (lightweight)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

FROM dependencies AS production

ARG PROVIDER
ARG WHISPER_MODEL_SIZE

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package transcribe --extra "${PROVIDER}"

ENV HF_HOME=/opt/whisper-cache \
    WHISPER_MODEL_SIZE=${WHISPER_MODEL_SIZE}

RUN mkdir -p "$HF_HOME" && \
    if [ "$PROVIDER" = "whisper" ]; then \
        python -c "import os; from faster_whisper import WhisperModel; WhisperModel(os.environ['WHISPER_MODEL_SIZE'], device='cpu', compute_type='int8')"; \
    fi

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /workspace /opt/whisper-cache
USER appuser

WORKDIR /workspace/services/transcribe

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
