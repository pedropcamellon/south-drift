"""Backend-local dataclass workflow payloads used for Temporal start requests."""

from dataclasses import dataclass


@dataclass
class AudioReference:
    storage_key: str
    audio_url: str
    original_filename: str | None = None
    content_type: str | None = None


@dataclass
class VoiceNotesInput:
    encounter_id: str
    patient_id: str
    audio: AudioReference


def build_voicenotes_input(
    encounter_id: str,
    patient_id: str,
    storage_key: str,
    audio_url: str,
    original_filename: str | None,
    content_type: str | None,
) -> VoiceNotesInput:
    return VoiceNotesInput(
        encounter_id=encounter_id,
        patient_id=patient_id,
        audio=AudioReference(
            storage_key=storage_key,
            audio_url=audio_url,
            original_filename=original_filename,
            content_type=content_type,
        ),
    )
