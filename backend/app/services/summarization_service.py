"""Summarization service client for calling summarization microservice"""

import logging
from typing import Protocol, cast

import httpx
from pydantic import ValidationError

from app.config import settings
from app.core.exceptions import AIServiceError
from app.models.summarization import SummarizationResponse

logger = logging.getLogger(__name__)


class SummarizationSettings(Protocol):
    SUMMARIZATION_SERVICE_URL: str


summarization_settings = cast(SummarizationSettings, settings)


class SummarizationService:
    """Client for summarization microservice"""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or summarization_settings.SUMMARIZATION_SERVICE_URL
        self.timeout = 180.0  # 3 minutes for summarization (CPU-based LLM can be slow)

    async def summarize(
        self,
        transcript: str,
        format: str = "soap",
        encounter_type: str | None = None,
        language: str = "en",
    ) -> SummarizationResponse:
        """
        Generate clinical summary from transcript.

        Args:
            transcript: Transcribed text to summarize
            format: "soap" for SOAP notes, "narrative" for free-text
            encounter_type: Type of encounter (optional)
            language: Language code (default: "en")
        """
        logger.info(f"[REQUEST] Requesting summarization from {self.base_url}")
        logger.info(f"[INFO] Transcript length: {len(transcript)} chars, Format: {format}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                payload = {
                    "transcript": transcript,
                    "format": format,
                    "language": language,
                }
                if encounter_type:
                    payload["encounter_type"] = encounter_type

                logger.debug(f"[DEBUG] Payload: {payload}")

                response = await client.post(
                    f"{self.base_url}/summarize",
                    json=payload,
                )

                response.raise_for_status()
                result = SummarizationResponse.model_validate(response.json())

                logger.info(f"[OK] Summarization complete ({result.processing_time:.2f}s)")
                logger.debug(f"[DEBUG] Summary length: {len(result.summary)}")

                return result

            except httpx.TimeoutException:
                logger.error(f"[ERROR] Summarization timed out after {self.timeout}s")
                raise AIServiceError("summarization", "request timed out")

            except httpx.HTTPStatusError as e:
                logger.error(f"[ERROR] Summarization failed: {e.response.status_code}")
                logger.error(f"[ERROR] Response: {e.response.text}")
                raise AIServiceError("summarization", f"upstream returned {e.response.status_code}")

            except httpx.RequestError as exc:
                logger.error(f"[ERROR] Summarization request failed: {exc}")
                raise AIServiceError("summarization", "request failed") from exc

            except ValidationError as exc:
                logger.error(f"[ERROR] Invalid summarization response: {exc}")
                raise AIServiceError("summarization", "returned an invalid response") from exc

    async def health_check(self) -> bool:
        """Check if summarization service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning(f"[WARN] Summarization service health check failed: {exc}")
            return False
