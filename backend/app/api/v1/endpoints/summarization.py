"""Summarization endpoints - test integration with summarization service"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.dependencies import get_summarization_service
from app.models.summarization import SummarizationResponse
from app.services.summarization_service import SummarizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summarization", tags=["summarization"])


class SummarizeRequest(BaseModel):
    """Request model for summarization"""

    transcript: str
    format: str = "soap"
    encounter_type: str | None = None
    language: str = "en"


@router.post("", response_model=SummarizationResponse)
async def summarize_transcript(
    request: SummarizeRequest,
    _: object = Depends(require_permission(Permission.ENCOUNTERS_SUMMARIZE)),
    service: SummarizationService = Depends(get_summarization_service),
) -> SummarizationResponse:
    """
    Generate a clinical summary from transcript text.
    """
    return await service.summarize(
        transcript=request.transcript,
        format=request.format,
        encounter_type=request.encounter_type,
        language=request.language,
    )


@router.get("/health")
async def check_summarization_health(
    _: object = Depends(require_permission(Permission.ADMIN_HEALTH_READ)),
    service: SummarizationService = Depends(get_summarization_service),
):
    """Check if summarization service is reachable"""
    is_healthy = await service.health_check()
    return {
        "service": "summarization",
        "status": "healthy" if is_healthy else "unhealthy",
        "url": service.base_url,
    }
