"""Patient encounter endpoints and encounter-owned workflows."""

from secrets import compare_digest
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from folium.core.chart_review import ChartReviewHistoryRequest, ChartReviewHistoryResponse

from app.config import settings
from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.dependencies import (
    get_chart_review_request_service,
    get_encounter_service,
    get_voice_note_service,
)
from app.models.chart_review import ChartReviewResponse
from app.models.clinical import (
    EncounterCreate,
    EncounterNarrativeCreate,
    EncounterNarrativeResponse,
    EncounterNarrativeUpdate,
    EncounterResponse,
    EncounterUpdate,
    VoiceNoteUploadResponse,
    VoiceNoteWorkflowStartResponse,
    VoiceNoteWorkflowStatusResponse,
)
from app.models.user import User
from app.services.chart_review_request_service import ChartReviewRequestService
from app.services.encounter_service import EncounterService
from app.services.voice_note_service import VoiceNoteService

router = APIRouter(prefix="/encounters")


@router.get("/", response_model=list[EncounterResponse])
async def list_encounters(
    patient_id: UUID = Query(..., alias="patientId"),
    _: User = Depends(require_permission(Permission.ENCOUNTERS_READ)),
    service: EncounterService = Depends(get_encounter_service),
) -> list[EncounterResponse]:
    return await service.list_by_patient_id(patient_id)


@router.get("/{encounter_id}", response_model=EncounterResponse)
async def get_encounter(
    encounter_id: UUID,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_READ)),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    return await service.get_by_id(encounter_id)


@router.post("/", response_model=EncounterResponse, status_code=status.HTTP_201_CREATED)
async def create_encounter(
    encounter_input: EncounterCreate,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_CREATE)),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    try:
        return await service.create(encounter_input)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.put("/{encounter_id}", response_model=EncounterResponse)
async def update_encounter(
    encounter_id: UUID,
    encounter_input: EncounterUpdate,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_UPDATE)),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    return await service.update(encounter_id, encounter_input)


@router.patch("/{encounter_id}/note", response_model=EncounterResponse)
async def replace_encounter_note(
    encounter_id: UUID,
    narrative_input: EncounterNarrativeUpdate,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_UPDATE)),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    return await service.replace_narrative(encounter_id, narrative_input)


@router.patch("/{encounter_id}/summary", response_model=EncounterResponse)
async def update_encounter_summary(
    encounter_id: UUID,
    summary_input: EncounterUpdate,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_SUMMARIZE)),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterResponse:
    if summary_input.summary is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="summary is required",
        )
    return await service.update(encounter_id, summary_input)


@router.delete("/{encounter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_encounter(
    encounter_id: UUID,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_DELETE)),
    service: EncounterService = Depends(get_encounter_service),
) -> None:
    await service.delete(encounter_id)


@router.post(
    "/{encounter_id}/narratives",
    response_model=EncounterNarrativeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_encounter_narrative(
    encounter_id: UUID,
    narrative_input: EncounterNarrativeCreate,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_UPDATE)),
    service: EncounterService = Depends(get_encounter_service),
) -> EncounterNarrativeResponse:
    try:
        return await service.create_narrative(encounter_id, narrative_input)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post("/{encounter_id}/audio", response_model=VoiceNoteUploadResponse)
async def upload_encounter_audio(
    encounter_id: UUID,
    audio: UploadFile = File(...),
    _: User = Depends(require_permission(Permission.VOICE_RECORD)),
    voice_note_service: VoiceNoteService = Depends(get_voice_note_service),
) -> VoiceNoteUploadResponse:
    try:
        return await voice_note_service.upload_audio(
            encounter_id=str(encounter_id),
            filename=audio.filename,
            content_type=audio.content_type,
            audio_content=await audio.read(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{encounter_id}/audio")
async def get_encounter_audio(
    encounter_id: UUID,
    _: User = Depends(require_permission(Permission.VOICE_REVIEW)),
    voice_note_service: VoiceNoteService = Depends(get_voice_note_service),
) -> Response:
    try:
        audio_download = await voice_note_service.get_audio_download(str(encounter_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(
        content=audio_download.content,
        media_type=audio_download.media_type,
        headers={"Content-Disposition": f'inline; filename="{audio_download.filename}"'},
    )


@router.post("/{encounter_id}/transcribe", response_model=VoiceNoteWorkflowStartResponse)
async def transcribe_encounter_audio(
    encounter_id: UUID,
    _: User = Depends(require_permission(Permission.VOICE_REVIEW)),
    voice_note_service: VoiceNoteService = Depends(get_voice_note_service),
) -> VoiceNoteWorkflowStartResponse:
    try:
        workflow_execution = await voice_note_service.start_workflow(str(encounter_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return workflow_execution


@router.get("/{encounter_id}/voice-note-status", response_model=VoiceNoteWorkflowStatusResponse)
async def get_encounter_voice_note_status(
    encounter_id: UUID,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_READ)),
    voice_note_service: VoiceNoteService = Depends(get_voice_note_service),
) -> VoiceNoteWorkflowStatusResponse:
    return await voice_note_service.get_workflow_status(str(encounter_id))


@router.post("/{encounter_id}/chart-review", response_model=ChartReviewResponse)
async def request_encounter_chart_review(
    encounter_id: UUID,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_SUMMARIZE)),
    service: ChartReviewRequestService = Depends(get_chart_review_request_service),
) -> ChartReviewResponse:
    return await service.request_for_encounter(str(encounter_id))


@router.get("/{encounter_id}/chart-review", response_model=ChartReviewResponse | None)
async def get_encounter_chart_review(
    encounter_id: UUID,
    _: User = Depends(require_permission(Permission.ENCOUNTERS_READ)),
    service: ChartReviewRequestService = Depends(get_chart_review_request_service),
) -> ChartReviewResponse | None:
    return await service.get_for_encounter(str(encounter_id))


@router.post("/internal/chart-review/history", response_model=ChartReviewHistoryResponse)
async def retrieve_chart_review_history(
    request: ChartReviewHistoryRequest,
    internal_token: str = Header(..., alias="X-ChartReview-Internal-Token"),
    service: ChartReviewRequestService = Depends(get_chart_review_request_service),
) -> ChartReviewHistoryResponse:
    if not compare_digest(internal_token, settings.CHARTREVIEW_INTERNAL_TOKEN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal token")
    try:
        return await service.retrieve_prior_encounter_blocks(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
