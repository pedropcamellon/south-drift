"""Database access for queued chart-review requests."""

from uuid import UUID

from folium.core.chart_review import ChartReviewInput, ChartReviewOutput, ChartReviewStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db.chart_review import ChartReview, ChartReviewCitation, ChartReviewSourceRef


class ChartReviewRepository:
    """Persists immutable review inputs before Temporal execution starts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_queued(
        self, patient_id: UUID, encounter_id: UUID, review_input: ChartReviewInput
    ) -> ChartReview:
        """Create a queued review with a JSON-safe snapshot and source references."""
        chart_review = ChartReview(
            patient_id=patient_id,
            encounter_id=encounter_id,
            status=ChartReviewStatus.QUEUED.value,
            input_snapshot=review_input.model_dump(mode="json"),
            input_source_refs=[
                ChartReviewSourceRef(
                    source_id=source.source_id,
                    source_type=source.source_type.value,
                )
                for source in review_input.source_chunks
            ],
        )
        self.session.add(chart_review)
        await self.session.flush()
        return chart_review

    async def get_by_id(self, review_id: UUID) -> ChartReview | None:
        """Load a review and its traceable source references."""
        result = await self.session.execute(
            select(ChartReview)
            .where(ChartReview.id == review_id)
            .options(
                selectinload(ChartReview.input_source_refs),
                selectinload(ChartReview.cited_source_refs),
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_for_encounter(self, encounter_id: UUID) -> ChartReview | None:
        """Load the most recently requested review for an encounter."""
        result = await self.session.execute(
            select(ChartReview)
            .where(ChartReview.encounter_id == encounter_id)
            .options(
                selectinload(ChartReview.input_source_refs),
                selectinload(ChartReview.cited_source_refs),
            )
            .order_by(ChartReview.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def complete(self, chart_review: ChartReview, output: ChartReviewOutput) -> None:
        """Persist validated output and explicit model citations in one transaction."""
        chart_review.status = ChartReviewStatus.COMPLETED.value
        chart_review.output_json = output.model_dump(mode="json")
        chart_review.confidence = output.confidence.value
        chart_review.review_flags = output.review_flags
        chart_review.provider_name = output.provider_name
        chart_review.cited_source_refs = [
            ChartReviewCitation(source_id=source.source_id) for source in output.source_refs
        ]
        await self.session.commit()

    async def fail(self, chart_review: ChartReview, failure_message: str) -> None:
        """Persist a terminal workflow failure in one transaction."""
        chart_review.status = ChartReviewStatus.FAILED.value
        chart_review.failure_message = failure_message
        await self.session.commit()
