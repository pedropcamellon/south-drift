"""Bounded LangGraph definition for one chart-review draft."""

import json
import logging
import time
from datetime import timedelta
from pathlib import Path

import httpx
from folium.ai import load_prompt, parse_chat_completion, system_message, user_message
from folium.core.chart_review import (
    ChartReviewConfidence,
    ChartReviewHistoryRequest,
    ChartReviewHistoryResponse,
    ChartReviewInput,
    ChartReviewOutput,
    ChartReviewSourceChunk,
)
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field
from temporalio.common import RetryPolicy

from app.config import settings
from app.models import ChartReviewGraphState

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
CHART_REVIEW_PROMPT_PATH = PROMPTS_DIR / "chart_review.md"
CHART_REVIEW_HISTORY_DECISION_PROMPT_PATH = PROMPTS_DIR / "chart_review_history_decision.md"


class ChartReviewHistoryDecision(BaseModel):
    """One bounded agent-selected search over prior interaction content."""

    model_config = ConfigDict(extra="forbid")

    search_terms: list[str] = Field(default_factory=list, max_length=3)


async def decide_history(
    state: ChartReviewGraphState,
) -> dict[str, list[str]]:
    """Temporal Activity that calls the provider to decide whether history is needed."""
    review_input = ChartReviewInput.model_validate(state["review_input"])
    active_context = "\n\n".join(
        f"[{source.source_id}] {source.source_type.value}: {source.content}"
        for source in review_input.source_chunks
    )
    messages = [
        system_message(load_prompt(CHART_REVIEW_HISTORY_DECISION_PROMPT_PATH)),
        user_message(f"Active interaction context:\n{active_context}"),
    ]
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.post(
            f"{settings.ai_service_base_url}/v1/chat/completions",
            json={
                "model": settings.ai_model_name,
                "messages": messages,
                "temperature": 0,
                "max_tokens": settings.history_decision_max_tokens,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        completion = parse_chat_completion(response.json())
        content = completion.content
    decision = ChartReviewHistoryDecision.model_validate_json(content)
    logger.info("Chart-review history decision: search_terms=%s", decision.search_terms)
    return {"history_search_terms": decision.search_terms}


async def retrieve_history(state: ChartReviewGraphState) -> dict[str, list[ChartReviewSourceChunk]]:
    """Temporal Activity that calls the backend's bounded history tool once."""
    review_input = ChartReviewInput.model_validate(state["review_input"])
    search_terms = state.get("history_search_terms", [])
    if not search_terms:
        return {"historical_source_chunks": []}
    request = ChartReviewHistoryRequest(
        patient_id=review_input.patient_id,
        encounter_id=review_input.encounter_id,
        search_terms=search_terms,
    )
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.post(
            f"{settings.chartreview_backend_url}/api/v1/encounters/internal/chart-review/history",
            headers={"X-ChartReview-Internal-Token": settings.chartreview_internal_token},
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()
    history = ChartReviewHistoryResponse.model_validate(response.json())
    if any(chunk.resource_id == review_input.encounter_id for chunk in history.source_chunks):
        raise ValueError("Chart-review history retrieval returned the active encounter")
    logger.info("Retrieved %d bounded prior chart-review source blocks", len(history.source_chunks))
    return {"historical_source_chunks": history.source_chunks}


async def generate_review(state: ChartReviewGraphState) -> dict[str, ChartReviewOutput]:
    """Temporal Activity that calls the provider with approved chart-review context."""
    review_input = ChartReviewInput.model_validate(state["review_input"])
    active_context = "\n\n".join(
        f"[{source.source_id}] {source.source_type.value}: {source.content}"
        for source in review_input.source_chunks
    )
    historical_source_chunks = [
        ChartReviewSourceChunk.model_validate(source)
        for source in state.get("historical_source_chunks", [])
    ]
    historical_context = "\n\n".join(
        f"[{source.source_id}] {source.source_type.value}: {source.content}"
        for source in historical_source_chunks
    )
    allowed_source_ids = [
        *(source.source_id for source in review_input.source_chunks),
        *(source.source_id for source in historical_source_chunks),
    ]
    messages = [
        system_message(load_prompt(CHART_REVIEW_PROMPT_PATH)),
        user_message(
            f"Allowed source IDs: {json.dumps(allowed_source_ids)}\n\n"
            f"Active interaction context:\n{active_context}\n\n"
            f"Approved prior interaction context:\n{historical_context or 'None supplied.'}"
        ),
    ]
    started_at = time.monotonic()
    logger.info(
        "Starting chart-review generation: encounter_id=%s source_chunks=%d max_tokens=%d",
        review_input.encounter_id,
        len(allowed_source_ids),
        settings.review_max_tokens,
    )
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ai_service_base_url}/v1/chat/completions",
                json={
                    "model": settings.ai_model_name,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": settings.review_max_tokens,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            completion = parse_chat_completion(response.json())
            content = completion.content
        logger.info(
            "Chart-review generation provider response received: encounter_id=%s response_characters=%d",
            review_input.encounter_id,
            len(content),
        )
    except httpx.HTTPError:
        logger.exception(
            "Chart-review generation provider request failed: encounter_id=%s elapsed_seconds=%.2f",
            review_input.encounter_id,
            time.monotonic() - started_at,
        )
        raise
    finally:
        logger.info(
            "Chart-review generation request ended: encounter_id=%s elapsed_seconds=%.2f",
            review_input.encounter_id,
            time.monotonic() - started_at,
        )
    logger.info("MediPhi raw chart-review completion: %s", content)
    try:
        raw_output = json.loads(content)
        normalized_output = _normalize_output(raw_output)
        normalized_output["provider_name"] = settings.ai_provider_name
        review_output = ChartReviewOutput.model_validate(normalized_output)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("MediPhi invalid chart-review completion: raw=%s error=%s", content, exc)
        raise

    logger.info(
        "MediPhi chart-review response validated: cited_sources=%d confidence=%s",
        len(review_output.source_refs),
        review_output.confidence,
    )
    valid_source_ids = set(allowed_source_ids)
    if any(source.source_id not in valid_source_ids for source in review_output.source_refs):
        logger.error(
            "MediPhi cited unknown source: raw=%s allowed_source_ids=%s",
            raw_output,
            allowed_source_ids,
        )
        raise ValueError("MediPhi returned a source reference outside the supplied snapshot")
    return {"review_output": review_output}


def _normalize_output(output: dict) -> dict:
    """Normalize bounded local-model JSON variations before strict contract validation."""
    source_refs = output.get("source_refs")
    if isinstance(source_refs, list):
        output["source_refs"] = [_normalize_source_ref(source_ref) for source_ref in source_refs]

    confidence = output.get("confidence")
    if isinstance(confidence, str):
        confidence_level, separator, confidence_explanation = confidence.partition("-")
        normalized_confidence = confidence_level.strip().lower()
        if normalized_confidence in {level.value for level in ChartReviewConfidence}:
            output["confidence"] = normalized_confidence
            if separator and confidence_explanation.strip() and not output.get("reasoning"):
                output["reasoning"] = confidence_explanation.strip()

    return output


def _normalize_source_ref(source_ref: object) -> object:
    """Accept known local-provider citation variants before strict validation."""
    if isinstance(source_ref, str):
        return {"source_id": source_ref}
    if (
        isinstance(source_ref, dict)
        and len(source_ref) == 1
        and next(iter(source_ref.values())) is True
    ):
        return {"source_id": next(iter(source_ref))}
    return source_ref


def build_chartreview_graph() -> StateGraph:
    graph = StateGraph(ChartReviewGraphState)
    graph.add_node(
        "decide_history",
        decide_history,
        metadata={
            "execute_in": "activity",
            "start_to_close_timeout": timedelta(
                seconds=settings.activity_start_to_close_timeout_seconds
            ),
            "retry_policy": RetryPolicy(maximum_attempts=settings.activity_max_attempts),
        },
    )
    graph.add_node(
        "retrieve_history",
        retrieve_history,
        metadata={
            "execute_in": "activity",
            "start_to_close_timeout": timedelta(
                seconds=settings.activity_start_to_close_timeout_seconds
            ),
            "retry_policy": RetryPolicy(maximum_attempts=settings.activity_max_attempts),
        },
    )
    graph.add_node(
        "generate_review",
        generate_review,
        metadata={
            "execute_in": "activity",
            "start_to_close_timeout": timedelta(
                seconds=settings.activity_start_to_close_timeout_seconds
            ),
            "retry_policy": RetryPolicy(maximum_attempts=settings.activity_max_attempts),
        },
    )
    graph.add_edge(START, "decide_history")
    graph.add_edge("decide_history", "retrieve_history")
    graph.add_edge("retrieve_history", "generate_review")
    graph.add_edge("generate_review", END)
    return graph
