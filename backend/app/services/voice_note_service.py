"""Voice note application service for upload, workflow orchestration, and status lookup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.models.clinical import (
    EncounterAudioMetadata,
    EncounterNarrativeUpdate,
    EncounterUpdate,
    TranscriptionStatus,
    VoiceNoteUploadResponse,
    VoiceNoteWorkflowMetadata,
    VoiceNoteWorkflowStartResponse,
    VoiceNoteWorkflowStatus,
    VoiceNoteWorkflowStatusResponse,
)
from app.services.encounter_service import EncounterService
from app.services.storage.base import ObjectStorageProvider
from app.services.voicenotes import VoiceNotesService


@dataclass(frozen=True)
class AudioDownload:
    content: bytes
    media_type: str
    filename: str


class VoiceNoteService:
    """Coordinates object storage, encounter updates, and Temporal workflow state."""

    def __init__(
        self,
        encounter_service: EncounterService,
        workflow_service: VoiceNotesService,
        storage_provider: ObjectStorageProvider,
    ) -> None:
        self.encounter_service = encounter_service
        self.workflow_service = workflow_service
        self.storage_provider = storage_provider

    async def upload_audio(
        self,
        encounter_id: str,
        filename: str | None,
        content_type: str | None,
        audio_content: bytes,
    ) -> VoiceNoteUploadResponse:
        storage_key = f"audio/{encounter_id}/{uuid4()}_{filename}"
        storage_url = await self.storage_provider.upload(
            key=storage_key,
            data=audio_content,
            content_type=content_type or "audio/webm",
        )

        audio_metadata = EncounterAudioMetadata(
            filename=filename,
            storage_key=storage_key,
            storage_url=storage_url,
            size=len(audio_content),
            content_type=content_type,
        )

        await self.encounter_service.update(
            UUID(encounter_id), EncounterUpdate(audioMetadata=audio_metadata)
        )

        workflow_execution = await self.start_workflow(encounter_id)
        return VoiceNoteUploadResponse(
            encounter_id=UUID(encounter_id),
            filename=filename,
            storage_key=storage_key,
            storage_url=storage_url,
            size=len(audio_content),
            workflow_id=workflow_execution.workflow_id,
            run_id=workflow_execution.run_id,
            message="Audio uploaded. Voice note workflow started.",
        )

    async def get_audio_download(self, encounter_id: str) -> AudioDownload:
        encounter = await self.encounter_service.get_by_id(UUID(encounter_id))
        audio_data = encounter.audio_metadata or EncounterAudioMetadata()
        storage_key = audio_data.storage_key

        if not storage_key:
            raise ValueError("No audio found for this encounter")

        audio_bytes = await self.storage_provider.download(storage_key)
        return AudioDownload(
            content=audio_bytes,
            media_type=audio_data.content_type or "audio/webm",
            filename=audio_data.filename or "audio.webm",
        )

    async def start_workflow(self, encounter_id: str) -> VoiceNoteWorkflowStartResponse:
        encounter = await self.encounter_service.get_by_id(UUID(encounter_id))
        audio_data = encounter.audio_metadata or EncounterAudioMetadata()
        storage_key = audio_data.storage_key

        if not storage_key:
            raise ValueError("No audio uploaded for this encounter")

        presigned_url = await self.storage_provider.get_presigned_url(
            storage_key,
            expiration=3600,
            internal=True,
        )

        workflow_execution = await self.workflow_service.start_voicenotes(
            encounter_id=encounter_id,
            patient_id=str(encounter.patient_id),
            storage_key=storage_key,
            audio_url=presigned_url,
            original_filename=audio_data.filename,
            content_type=audio_data.content_type,
        )

        audio_data = audio_data.model_copy(
            update={
                "transcription_status": TranscriptionStatus.PROCESSING,
                "workflow": VoiceNoteWorkflowMetadata(
                    workflow_id=workflow_execution["workflowId"],
                    run_id=workflow_execution["runId"],
                    status=TranscriptionStatus.PROCESSING,
                    updated_at=self._now(),
                ),
            }
        )

        await self.encounter_service.update(
            UUID(encounter_id), EncounterUpdate(audioMetadata=audio_data)
        )
        return VoiceNoteWorkflowStartResponse(
            encounter_id=UUID(encounter_id),
            workflow_id=workflow_execution["workflowId"],
            run_id=workflow_execution["runId"],
            message="Voice note workflow started.",
        )

    async def get_workflow_status(self, encounter_id: str) -> VoiceNoteWorkflowStatusResponse:
        encounter = await self.encounter_service.get_by_id(UUID(encounter_id))
        audio_data = encounter.audio_metadata or EncounterAudioMetadata()
        workflow_metadata = audio_data.workflow or VoiceNoteWorkflowMetadata()
        workflow_id = workflow_metadata.workflow_id
        run_id = workflow_metadata.run_id

        if not workflow_id:
            return VoiceNoteWorkflowStatusResponse(
                encounter_id=UUID(encounter_id),
                status=VoiceNoteWorkflowStatus.IDLE,
                encounter=encounter,
            )

        workflow_state = await self.workflow_service.get_voicenotes_state(workflow_id, run_id)
        temporal_status = workflow_state["status"]
        status_value = VoiceNoteWorkflowStatus.PROCESSING
        error_message = workflow_state.get("errorMessage")

        if temporal_status == "completed":
            result = workflow_state.get("result") or {}
            status_value = VoiceNoteWorkflowStatus(result.get("status", "completed"))
            encounter = await self._apply_workflow_result(encounter_id, workflow_state)
        elif temporal_status in {"failed", "canceled", "terminated", "timed_out"}:
            status_value = VoiceNoteWorkflowStatus.FAILED
            encounter = await self._mark_workflow_failed(
                encounter_id,
                audio_data,
                workflow_metadata,
                error_message,
            )

        return VoiceNoteWorkflowStatusResponse(
            encounter_id=UUID(encounter_id),
            workflow_id=workflow_id,
            run_id=run_id,
            status=status_value,
            failure_stage=workflow_metadata.failure_stage
            or (workflow_state.get("result") or {}).get("failure_stage"),
            error_message=error_message or workflow_metadata.error_message,
            encounter=encounter,
        )

    async def _apply_workflow_result(self, encounter_id: str, workflow_state: dict):
        encounter = await self.encounter_service.get_by_id(UUID(encounter_id))
        audio_data = encounter.audio_metadata or EncounterAudioMetadata()
        workflow_metadata = audio_data.workflow or VoiceNoteWorkflowMetadata()

        if workflow_metadata.transcript_applied_at:
            return encounter

        result = workflow_state.get("result") or {}
        result_status = result.get("status", "completed")
        transcript = result.get("transcript")
        error_message = result.get("error_message") or workflow_state.get("errorMessage")

        audio_data = audio_data.model_copy(
            update={
                "transcription_status": TranscriptionStatus(result_status),
                "workflow": VoiceNoteWorkflowMetadata(
                    workflow_id=workflow_state.get("workflowId"),
                    run_id=workflow_state.get("runId"),
                    status=TranscriptionStatus(result_status),
                    failure_stage=result.get("failure_stage"),
                    error_message=error_message,
                    updated_at=self._now(),
                    transcript_applied_at=self._now(),
                ),
            }
        )

        encounter = await self.encounter_service.update(
            UUID(encounter_id), EncounterUpdate(audioMetadata=audio_data)
        )
        if transcript:
            encounter = await self.encounter_service.replace_narrative(
                UUID(encounter_id),
                EncounterNarrativeUpdate(content=transcript),
            )

        return encounter

    async def _mark_workflow_failed(
        self,
        encounter_id: str,
        audio_data: EncounterAudioMetadata,
        workflow_metadata: VoiceNoteWorkflowMetadata,
        error_message: str | None,
    ):
        updated_audio_data = audio_data.model_copy(
            update={
                "transcription_status": TranscriptionStatus.FAILED,
                "workflow": workflow_metadata.model_copy(
                    update={
                        "status": TranscriptionStatus.FAILED,
                        "error_message": error_message,
                        "updated_at": self._now(),
                    }
                ),
            }
        )
        return await self.encounter_service.update(
            UUID(encounter_id), EncounterUpdate(audioMetadata=updated_audio_data)
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
