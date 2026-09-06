"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from typing import Protocol, cast

from azure.core.exceptions import AzureError
from botocore.exceptions import BotoCoreError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.endpoints.auth import auth_router, users_router
from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import setup_structured_logging
from app.core.metrics import PrometheusMiddleware, metrics_endpoint
from app.core.middleware import CorrelationMiddleware

# Set up structured JSON logging with audit support
logger = setup_structured_logging("backend")


class ApplicationSettings(Protocol):
    app_name: str
    version: str
    ALLOWED_ORIGINS: list[str]


app_settings = cast(ApplicationSettings, settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler"""
    # Startup
    logger.info(f"{app_settings.app_name} v{app_settings.version} starting...")
    logger.info("API documentation available at: /docs")

    # Schema migrations run before Uvicorn starts in Docker Compose.
    from app.core.database import async_session_maker, verify_database_connection

    await verify_database_connection()

    # Initialize storage before creating stored document attachments.
    from app.services.storage import get_storage

    try:
        storage = await get_storage()
        logger.info(
            f"Storage initialized: {storage.config.provider.upper()} - {storage.config.bucket}"
        )
    except (AzureError, BotoCoreError, OSError, ValueError) as exc:
        logger.warning(f"Storage initialization failed: {exc}")
        storage = None

    # Seed test data
    try:
        from app.seed import (
            seed_clinical_documents,
            seed_diagnostic_reports,
            seed_encounters,
            seed_imaging_studies,
            seed_patients,
            seed_users,
        )

        async with async_session_maker() as session:
            await seed_users(session)
            patients = await seed_patients(session)
            if patients:
                await seed_encounters(session, patients)
                await seed_diagnostic_reports(session, patients)
                await seed_imaging_studies(session, patients)
                if storage is not None:
                    await seed_clinical_documents(session, storage, patients)
        logger.info("Database seeding complete")
    except (AzureError, BotoCoreError, OSError, SQLAlchemyError, ValueError) as exc:
        logger.warning(f"Failed to seed database: {exc}")

    # Check transcription service health
    from app.services.transcription_service import get_transcription_service

    try:
        transcription_svc = get_transcription_service()
        health = await transcription_svc.health_check()
        if health.get("status") == "healthy":
            provider = health.get("provider", "unknown")
            logger.info(f"Transcription service healthy: {provider}")
        else:
            logger.warning(f"Transcription service unhealthy: {health.get('error', 'Unknown')}")
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning(f"Transcription service unavailable: {exc}")

    yield

    # Shutdown
    logger.info(f"{app_settings.app_name} shutting down...")


# Create FastAPI app
app = FastAPI(
    title=app_settings.app_name,
    description="Healthcare platform backend with AI capabilities",
    version=app_settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware for request tracing
app.add_middleware(CorrelationMiddleware)

# Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Include API router with v1 prefix
app.include_router(api_router, prefix="/api/v1")

# Include authentication routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": app_settings.version, "app": app_settings.app_name}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return metrics_endpoint()
