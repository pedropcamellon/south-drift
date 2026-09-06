from datetime import timedelta

from folium.core.voicenotes import TRANSCRIBE_ACTIVITY_NAME, VOICENOTES_WORKFLOW_NAME
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

from app.contracts.voice_note_models import (
    TranscriptionResult,
    VoiceNoteWorkflowInput,
    VoiceNoteWorkflowResult,
    VoiceNoteWorkflowStatus,
)


@workflow.defn(name=VOICENOTES_WORKFLOW_NAME)
class VoiceNoteWorkflow:
    @workflow.run
    async def run(self, input_data: VoiceNoteWorkflowInput) -> VoiceNoteWorkflowResult:
        retry_policy = RetryPolicy(maximum_attempts=3, backoff_coefficient=2.0)

        try:
            transcript_result = await workflow.execute_activity(
                TRANSCRIBE_ACTIVITY_NAME,
                args=[input_data.audio],
                result_type=TranscriptionResult,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )
        except Exception as exc:
            workflow.logger.error("Voice note transcription stage failed: %s", exc)
            raise ApplicationError(
                f"Voice note transcription failed: {exc}",
                type="transcription",
            )

        return VoiceNoteWorkflowResult(
            encounter_id=input_data.encounter_id,
            status=VoiceNoteWorkflowStatus.COMPLETED,
            transcript_saved=True,
            transcript=transcript_result.transcript,
        )
