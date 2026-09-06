"""Chart-review database models for durable draft-support requests."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base

if TYPE_CHECKING:
    from app.models.db.clinical import Encounter
    from app.models.db.patient import Patient


class ChartReview(Base):
    """Persisted chart-review request and its immutable source snapshot."""

    __tablename__ = "chart_review"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[UUID] = mapped_column(
        ForeignKey("encounter.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)
    review_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    provider_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=True,
    )

    patient: Mapped["Patient"] = relationship("Patient")
    encounter: Mapped["Encounter"] = relationship("Encounter")
    input_source_refs: Mapped[list["ChartReviewSourceRef"]] = relationship(
        "ChartReviewSourceRef", back_populates="chart_review", cascade="all, delete-orphan"
    )
    cited_source_refs: Mapped[list["ChartReviewCitation"]] = relationship(
        "ChartReviewCitation", back_populates="chart_review", cascade="all, delete-orphan"
    )


class ChartReviewSourceRef(Base):
    """Traceable source identifier retained without copying source content."""

    __tablename__ = "chart_review_source_ref"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    chart_review_id: Mapped[UUID] = mapped_column(
        ForeignKey("chart_review.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)

    chart_review: Mapped["ChartReview"] = relationship(
        "ChartReview", back_populates="input_source_refs"
    )


class ChartReviewCitation(Base):
    """A source explicitly cited by validated chart-review output."""

    __tablename__ = "chart_review_citation"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    chart_review_id: Mapped[UUID] = mapped_column(
        ForeignKey("chart_review.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)

    chart_review: Mapped["ChartReview"] = relationship(
        "ChartReview", back_populates="cited_source_refs"
    )
