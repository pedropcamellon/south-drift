"""Self-hosted Whisper transcription provider (HIPAA compliant)"""

import logging
import os
import tempfile
import time

import httpx

from app.config import settings

from .base import TranscriptionProvider

logger = logging.getLogger(__name__)


class WhisperProvider(TranscriptionProvider):
    """
    Self-hosted Whisper transcription using faster-whisper.

    Advantages:
    - HIPAA compliant (PHI stays on-premise)
    - No BAA required
    - No usage costs
    - Works offline
    """

    def __init__(self):
        self.model = None

    async def initialize(self) -> None:
        """Load Whisper model on startup"""
        try:
            from faster_whisper import WhisperModel

            # The persistent HF_HOME volume is populated on first startup.
            self.model = WhisperModel(
                model_size_or_path=settings.WHISPER_MODEL_SIZE,
                device=settings.WHISPER_DEVICE,
                compute_type="int8" if settings.WHISPER_DEVICE == "cpu" else "float16",
                download_root=None,  # Use default HF_HOME cache location
            )
            print(
                f"[OK] Whisper model loaded from cache: {settings.WHISPER_MODEL_SIZE} on {settings.WHISPER_DEVICE}"
            )
        except ImportError:
            raise RuntimeError(
                "faster-whisper not installed. Run: uv pip install -e .[whisper]"
            )

    async def transcribe(
        self,
        audio_url: str,
        language_code: str = "en-US",
        speaker_labels: bool = False,
        vocabulary_name: str | None = None,
    ) -> dict:
        """Transcribe audio using Whisper"""
        start_time = time.time()

        # Download audio from presigned URL (works with any storage provider)
        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url, timeout=60.0)
            response.raise_for_status()
            audio_data = response.content

        # Save to temporary file (faster-whisper requires file path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        try:
            # Transcribe locally (no data leaves your infrastructure)
            language = language_code.split("-")[0]  # "en-US" → "en"

            logger.info(
                f"[TRANSCRIBE] Transcribing audio file: {temp_path} ({len(audio_data)} bytes)"
            )

            segments_iter, info = self.model.transcribe(
                temp_path,
                language=language,
                vad_filter=False,  # Disable aggressive VAD for short audio
                word_timestamps=True,
            )

            # Convert generator to list
            segments = list(segments_iter)

            logger.info(
                f"[INFO] Detected {len(segments)} segments, language: {info.language}"
            )

            # Format response
            transcript = " ".join([s.text.strip() for s in segments])

            logger.info(
                f"[INFO] Transcript generated ({len(transcript)} chars): {transcript[:100]}..."
            )

            processing_time = time.time() - start_time

            return {
                "transcript": transcript,
                "language_code": info.language,
                "confidence": None,  # Whisper doesn't provide overall confidence
                "segments": [
                    {
                        "start_time": s.start,
                        "end_time": s.end,
                        "text": s.text.strip(),
                        "confidence": None,
                        "speaker_label": None,  # Speaker diarization not built-in
                    }
                    for s in segments
                ],
                "processing_time": processing_time,
                "job_id": None,
            }
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def get_provider_name(self) -> str:
        return f"whisper-{settings.WHISPER_MODEL_SIZE}"
