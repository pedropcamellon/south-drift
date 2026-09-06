import logging
from typing import Any

import httpx

from app.contracts.voice_note_models import VoiceNoteWorkflowStatus

logger = logging.getLogger(__name__)


class BackendApiClient:
    def __init__(self, base_url: str, timeout_seconds: float, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.token = token

    async def mark_processing(self, encounter_id: str, workflow_id: str) -> dict[str, Any]:
        metadata = {
            "voiceNoteWorkflow": {
                "workflowId": workflow_id,
                "status": VoiceNoteWorkflowStatus.PROCESSING.value,
            }
        }
        return await self._patch_encounter(encounter_id, {"audioMetadata": metadata})

    async def save_transcript(self, encounter_id: str, transcript: str) -> dict[str, Any]:
        encounter = await self._get_encounter(encounter_id)
        metadata = self._workflow_metadata(encounter)
        metadata.update({"status": VoiceNoteWorkflowStatus.TRANSCRIBED.value})

        note = transcript.strip()
        payload: dict[str, Any] = {
            "content": note,
        }
        return await self._patch_encounter_narrative(encounter_id, payload)

    async def save_summary(
        self,
        encounter_id: str,
        summary: str,
        structured_summary: dict[str, Any] | None,
    ) -> dict[str, Any]:
        encounter = await self._get_encounter(encounter_id)
        metadata = self._workflow_metadata(encounter)
        metadata.update({"status": VoiceNoteWorkflowStatus.COMPLETED.value})

        payload: dict[str, Any] = {
            "summary": summary,
            "audioMetadata": {**self._existing_metadata(encounter), "voiceNoteWorkflow": metadata},
        }
        if structured_summary is not None:
            payload["structuredSummary"] = structured_summary

        return await self._patch_encounter(encounter_id, payload)

    async def mark_failed(
        self,
        encounter_id: str,
        workflow_id: str,
        stage: str,
        error_message: str,
        partial: bool,
    ) -> dict[str, Any]:
        encounter = await self._get_encounter(encounter_id)
        metadata = self._workflow_metadata(encounter)
        metadata.update(
            {
                "workflowId": workflow_id,
                "status": VoiceNoteWorkflowStatus.PARTIAL.value
                if partial
                else VoiceNoteWorkflowStatus.FAILED.value,
                "failureStage": stage,
                "errorMessage": error_message,
                "partial": partial,
            }
        )
        payload = {
            "audioMetadata": {**self._existing_metadata(encounter), "voiceNoteWorkflow": metadata}
        }
        return await self._patch_encounter(encounter_id, payload)

    async def _get_encounter(self, encounter_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/encounters/{encounter_id}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def _patch_encounter(self, encounter_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/encounters/{encounter_id}",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            logger.info("Encounter updated for workflow state")
            return response.json()

    async def _patch_encounter_narrative(
        self, encounter_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/encounters/{encounter_id}/note",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    @staticmethod
    def _existing_metadata(encounter: dict[str, Any]) -> dict[str, Any]:
        metadata = encounter.get("audioMetadata")
        return metadata if isinstance(metadata, dict) else {}

    def _workflow_metadata(self, encounter: dict[str, Any]) -> dict[str, Any]:
        metadata = self._existing_metadata(encounter)
        workflow_metadata = metadata.get("voiceNoteWorkflow")
        if isinstance(workflow_metadata, dict):
            return dict(workflow_metadata)
        return {}
