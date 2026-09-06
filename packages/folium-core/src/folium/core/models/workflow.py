"""Serializable contracts shared by voice-note workflow callers and workers."""

from dataclasses import dataclass

VOICENOTES_WORKFLOW_NAME = "voicenotes"
VOICENOTES_TASK_QUEUE = "voice-notes-queue"


@dataclass
class AudioReference:
    """Location and descriptive metadata for audio consumed by a workflow."""

    storage_key: str
    audio_url: str | None = None
    bucket: str | None = None
    original_filename: str | None = None
    content_type: str | None = None


@dataclass
class VoiceNotesInput:
    """Voice-note workflow input independent of persistence and transport layers."""

    encounter_id: str
    patient_id: str
    audio: AudioReference
