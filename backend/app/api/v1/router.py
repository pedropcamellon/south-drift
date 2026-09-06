"""Main API router for v1 endpoints"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    clinical_documents,
    diagnostic_reports,
    encounters,
    health,
    imaging_studies,
    patients,
    storage_test,
    summarization,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(patients.router, tags=["patients"])
api_router.include_router(encounters.router, tags=["encounters"])
api_router.include_router(diagnostic_reports.router, tags=["diagnostic-reports"])
api_router.include_router(imaging_studies.router, tags=["imaging-studies"])
api_router.include_router(clinical_documents.router, tags=["clinical-documents"])
api_router.include_router(storage_test.router, tags=["storage-test"])
api_router.include_router(summarization.router, tags=["summarization"])
