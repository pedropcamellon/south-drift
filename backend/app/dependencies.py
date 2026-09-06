"""Dependency injection for FastAPI"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.repositories.chart_review_repository import ChartReviewRepository
from app.repositories.clinical_document_repository import ClinicalDocumentRepository
from app.repositories.diagnostic_report_repository import DiagnosticReportRepository
from app.repositories.encounter_repository import EncounterRepository
from app.repositories.imaging_study_repository import ImagingStudyRepository
from app.repositories.patient_repository import PatientRepository
from app.services.chart_review_request_service import ChartReviewRequestService
from app.services.chart_review_workflow_service import ChartReviewWorkflowService
from app.services.clinical_document_service import ClinicalDocumentService
from app.services.diagnostic_report_service import DiagnosticReportService
from app.services.encounter_service import EncounterService
from app.services.imaging_study_service import ImagingStudyService
from app.services.patient_history_service import PatientHistoryService
from app.services.patient_service import PatientService
from app.services.storage.base import ObjectStorageProvider
from app.services.storage.factory import get_storage
from app.services.summarization_service import SummarizationService
from app.services.transcription_service import TranscriptionService
from app.services.voice_note_service import VoiceNoteService
from app.services.voicenotes import VoiceNotesService

# Singletons (for services without database dependencies)
_transcription_service = None
_summarization_service = None
_voicenotes_service = None
_chart_review_workflow_service = None


def get_patient_repository(session: AsyncSession = Depends(get_async_session)) -> PatientRepository:
    """Get patient repository with database session"""
    return PatientRepository(session)


def get_patient_service(
    repository: PatientRepository = Depends(get_patient_repository),
) -> PatientService:
    """Get patient service with injected repository"""
    return PatientService(repository)


def get_encounter_repository(
    session: AsyncSession = Depends(get_async_session),
) -> EncounterRepository:
    return EncounterRepository(session)


def get_encounter_service(
    repository: EncounterRepository = Depends(get_encounter_repository),
) -> EncounterService:
    return EncounterService(repository)


def get_clinical_document_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ClinicalDocumentRepository:
    return ClinicalDocumentRepository(session)


def get_clinical_document_service(
    repository: ClinicalDocumentRepository = Depends(get_clinical_document_repository),
) -> ClinicalDocumentService:
    return ClinicalDocumentService(repository)


def get_diagnostic_report_repository(
    session: AsyncSession = Depends(get_async_session),
) -> DiagnosticReportRepository:
    return DiagnosticReportRepository(session)


def get_diagnostic_report_service(
    repository: DiagnosticReportRepository = Depends(get_diagnostic_report_repository),
) -> DiagnosticReportService:
    return DiagnosticReportService(repository)


def get_imaging_study_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ImagingStudyRepository:
    return ImagingStudyRepository(session)


def get_imaging_study_service(
    repository: ImagingStudyRepository = Depends(get_imaging_study_repository),
) -> ImagingStudyService:
    return ImagingStudyService(repository)


def get_patient_history_service(
    encounter_service: EncounterService = Depends(get_encounter_service),
    diagnostic_report_service: DiagnosticReportService = Depends(get_diagnostic_report_service),
    imaging_study_service: ImagingStudyService = Depends(get_imaging_study_service),
) -> PatientHistoryService:
    return PatientHistoryService(
        encounter_service, diagnostic_report_service, imaging_study_service
    )


def get_chart_review_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ChartReviewRepository:
    """Get chart-review repository with database session."""
    return ChartReviewRepository(session)


def get_chart_review_request_service(
    repository: ChartReviewRepository = Depends(get_chart_review_repository),
    encounter_service: EncounterService = Depends(get_encounter_service),
    workflow_service: ChartReviewWorkflowService = Depends(
        lambda: get_chart_review_workflow_service()
    ),
) -> ChartReviewRequestService:
    """Get the explicit clinician-requested chart-review service."""
    return ChartReviewRequestService(repository, encounter_service, workflow_service)


def get_chart_review_workflow_service() -> ChartReviewWorkflowService:
    global _chart_review_workflow_service
    if _chart_review_workflow_service is None:
        _chart_review_workflow_service = ChartReviewWorkflowService()
    return _chart_review_workflow_service


def get_transcription_service() -> TranscriptionService:
    """Get transcription service instance (singleton)"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service


def get_summarization_service() -> SummarizationService:
    """Get summarization service instance (singleton)"""
    global _summarization_service
    if _summarization_service is None:
        _summarization_service = SummarizationService()
    return _summarization_service


def get_voicenotes_service() -> VoiceNotesService:
    """Get voicenotes service instance (singleton)."""
    global _voicenotes_service
    if _voicenotes_service is None:
        _voicenotes_service = VoiceNotesService()
    return _voicenotes_service


async def get_storage_provider() -> ObjectStorageProvider:
    """Get storage provider instance (singleton)"""
    return await get_storage()


async def get_voice_note_service(
    encounter_service: EncounterService = Depends(get_encounter_service),
    workflow_service: VoiceNotesService = Depends(get_voicenotes_service),
    storage_provider: ObjectStorageProvider = Depends(get_storage_provider),
) -> VoiceNoteService:
    """Get voice note orchestration service with injected collaborators."""
    return VoiceNoteService(encounter_service, workflow_service, storage_provider)
