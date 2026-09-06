"""On-demand chart-review request orchestration for the encounter API."""

import logging
from uuid import UUID

from folium.core.chart_review import (
    ChartReviewConfidence,
    ChartReviewHistoryRequest,
    ChartReviewHistoryResponse,
    ChartReviewInput,
    ChartReviewSourceChunk,
    ChartReviewSourceType,
    ChartReviewStatus,
    ChartReviewWorkflowInput,
)

from app.models.chart_review import ChartReviewCitationResponse, ChartReviewResponse
from app.models.db.chart_review import ChartReview
from app.repositories.chart_review_repository import ChartReviewRepository
from app.services.chart_review_workflow_service import ChartReviewWorkflowService
from app.services.encounter_service import EncounterService

logger = logging.getLogger(__name__)


class ChartReviewRequestService:
    """Builds active-encounter snapshots and starts durable chart-review workflows."""

    def __init__(
        self,
        repository: ChartReviewRepository,
        encounter_service: EncounterService,
        workflow_service: ChartReviewWorkflowService,
    ) -> None:
        self._repository = repository
        self._encounter_service = encounter_service
        self._workflow_service = workflow_service

    async def request_for_encounter(self, encounter_id: str) -> ChartReviewResponse:
        """Persist and generate a draft review for an explicitly selected encounter."""
        encounter = await self._encounter_service.get_by_id(UUID(encounter_id))
        review_input = await self._build_input(encounter_id)
        chart_review = await self._repository.create_queued(
            patient_id=encounter.patient_id,
            encounter_id=UUID(encounter_id),
            review_input=review_input,
        )
        await self._repository.session.commit()
        try:
            await self._workflow_service.start(
                ChartReviewWorkflowInput(review_id=str(chart_review.id), review_input=review_input)
            )
        except Exception:
            logger.exception("Chart review workflow dispatch failed for review %s", chart_review.id)
            await self._repository.fail(
                chart_review, "Chart review could not be started. Please try again."
            )
            return self._to_response(chart_review)

        await self._repository.session.commit()
        return self._to_response(chart_review)

    async def get_for_encounter(self, encounter_id: str) -> ChartReviewResponse | None:
        """Return the latest persisted review for the selected encounter."""
        encounter = await self._encounter_service.get_by_id(UUID(encounter_id))
        review = await self._repository.get_latest_for_encounter(UUID(encounter_id))
        if review is None:
            return None
        if review.patient_id != encounter.patient_id:
            return None
        await self._refresh_workflow_result(review)
        return self._to_response(review)

    async def retrieve_prior_encounter_blocks(
        self, request: ChartReviewHistoryRequest
    ) -> ChartReviewHistoryResponse:
        """Return a bounded set of patient-scoped prior encounter source blocks."""
        active_encounter = await self._encounter_service.get_by_id(UUID(request.encounter_id))
        if str(active_encounter.patient_id) != request.patient_id:
            raise ValueError("Chart-review history request does not match the active encounter")

        prior_encounters = await self._encounter_service.list_by_patient_id(
            UUID(request.patient_id)
        )
        source_chunks: list[ChartReviewSourceChunk] = []
        for encounter in prior_encounters:
            if str(encounter.id) == request.encounter_id:
                continue
            for chunk in self._history_chunks_matching_terms(encounter, request.search_terms):
                source_chunks.append(
                    ChartReviewSourceChunk(
                        source_id=f"history-{chunk.source_id}",
                        source_type=chunk.source_type,
                        content=chunk.content,
                        resource_id=chunk.resource_id,
                        display_label=chunk.display_label,
                        content_role=chunk.content_role,
                        occurred_at=chunk.occurred_at,
                    )
                )
                if len(source_chunks) == request.max_blocks:
                    return ChartReviewHistoryResponse(source_chunks=source_chunks)
        return ChartReviewHistoryResponse(source_chunks=source_chunks)

    @staticmethod
    def _history_chunks_matching_terms(
        encounter, search_terms: list[str]
    ) -> list[ChartReviewSourceChunk]:
        """Return curated encounter blocks matching the agent's bounded search terms."""
        note_chunk = ChartReviewRequestService._transcript_chunk(encounter)
        candidate_chunks = ChartReviewRequestService._selected_encounter_chunks(encounter)
        if note_chunk is not None:
            candidate_chunks.append(note_chunk)
        return [
            chunk
            for chunk in candidate_chunks
            if any(term.casefold() in chunk.content.casefold() for term in search_terms)
        ]

    async def _build_input(self, encounter_id: str) -> ChartReviewInput:
        encounter = await self._encounter_service.get_by_id(UUID(encounter_id))
        selected_chunks = self._selected_encounter_chunks(encounter)
        return ChartReviewInput(
            patient_id=str(encounter.patient_id),
            encounter_id=encounter_id,
            encounters=selected_chunks,
            documents=[],
            transcript=self._transcript_chunk(encounter),
        )

    async def _refresh_workflow_result(self, chart_review: ChartReview) -> None:
        if chart_review.status in {
            ChartReviewStatus.COMPLETED.value,
            ChartReviewStatus.FAILED.value,
        }:
            return
        try:
            status, output, failure_message = await self._workflow_service.get_result(
                self._workflow_service.workflow_id(str(chart_review.id)), None
            )
        except Exception:
            logger.exception(
                "Chart review workflow status lookup failed for review %s", chart_review.id
            )
            await self._repository.fail(
                chart_review, "Chart review status could not be retrieved. Please try again."
            )
            return

        if status == "completed" and output is not None:
            await self._repository.complete(chart_review, output)
        elif status == "failed":
            await self._repository.fail(
                chart_review, failure_message or "Chart review workflow failed."
            )
        else:
            chart_review.status = ChartReviewStatus.RUNNING.value
            await self._repository.session.commit()

    @staticmethod
    def _selected_encounter_chunks(encounter) -> list[ChartReviewSourceChunk]:
        chunks: list[ChartReviewSourceChunk] = []
        if encounter.summary:
            chunks.append(
                ChartReviewSourceChunk(
                    source_id=f"encounter-summary:{encounter.id}",
                    source_type=ChartReviewSourceType.ENCOUNTER,
                    content=encounter.summary,
                    resource_id=str(encounter.id),
                    display_label=encounter.title,
                    content_role="summary",
                    occurred_at=encounter.started_at,
                )
            )
        if encounter.description:
            chunks.append(
                ChartReviewSourceChunk(
                    source_id=f"encounter-description:{encounter.id}",
                    source_type=ChartReviewSourceType.ENCOUNTER,
                    content=encounter.description,
                    resource_id=str(encounter.id),
                    display_label=encounter.title,
                    content_role="description",
                    occurred_at=encounter.started_at,
                )
            )
        if not chunks:
            chunks.append(
                ChartReviewSourceChunk(
                    source_id=f"encounter:{encounter.id}",
                    source_type=ChartReviewSourceType.ENCOUNTER,
                    content=encounter.title,
                    resource_id=str(encounter.id),
                    display_label=encounter.title,
                    content_role="title",
                    occurred_at=encounter.started_at,
                )
            )
        return chunks

    @staticmethod
    def _transcript_chunk(encounter) -> ChartReviewSourceChunk | None:
        if not encounter.note:
            return None
        return ChartReviewSourceChunk(
            source_id=f"encounter-note:{encounter.id}",
            source_type=ChartReviewSourceType.TRANSCRIPT,
            content=encounter.note,
            resource_id=str(encounter.id),
            display_label=encounter.title,
            content_role="voice-note transcript",
            occurred_at=encounter.started_at,
        )

    @staticmethod
    def _to_response(chart_review: ChartReview) -> ChartReviewResponse:
        output = chart_review.output_json or {}
        status = ChartReviewStatus(chart_review.status)
        source_refs = ChartReviewRequestService._public_source_refs(chart_review)
        return ChartReviewResponse(
            id=str(chart_review.id),
            encounterId=str(chart_review.encounter_id),
            status=status,
            summary=output.get("summary"),
            reasoning=output.get("reasoning"),
            missingInfo=output.get("missing_info", []),
            followUpQuestions=output.get("follow_up_questions", []),
            sourceRefs=source_refs,
            confidence=ChartReviewConfidence(chart_review.confidence)
            if chart_review.confidence
            else None,
            reviewFlags=chart_review.review_flags or [],
            failureMessage=chart_review.failure_message,
        )

    @staticmethod
    def _public_source_refs(chart_review: ChartReview) -> list[ChartReviewCitationResponse]:
        if ChartReviewStatus(chart_review.status) != ChartReviewStatus.COMPLETED:
            return []

        source_by_id = {
            source.source_id: source
            for source in ChartReviewInput.model_validate(chart_review.input_snapshot).source_chunks
        }
        return [
            ChartReviewCitationResponse(
                sourceType=source.source_type,
                resourceId=source.resource_id,
                displayLabel=source.display_label,
                contentRole=source.content_role,
                occurredAt=source.occurred_at,
            )
            for citation in chart_review.cited_source_refs
            if (source := source_by_id.get(citation.source_id)) is not None
        ]
