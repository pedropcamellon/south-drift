"""Backend response model plus shared chart-review workflow contracts."""

from datetime import datetime

from folium.core.chart_review import (
    ChartReviewConfidence,
    ChartReviewSourceType,
    ChartReviewStatus,
)
from pydantic import BaseModel, ConfigDict, Field


class ChartReviewCitationResponse(BaseModel):
    """Public display metadata for a cited immutable chart-review source."""

    model_config = ConfigDict(populate_by_name=True)

    source_type: ChartReviewSourceType = Field(..., alias="sourceType")
    resource_id: str | None = Field(None, alias="resourceId")
    display_label: str | None = Field(None, alias="displayLabel")
    content_role: str | None = Field(None, alias="contentRole")
    occurred_at: datetime | None = Field(None, alias="occurredAt")


class ChartReviewResponse(BaseModel):
    """Persisted draft-support review returned to the encounter UI."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    encounter_id: str = Field(..., alias="encounterId")
    status: ChartReviewStatus
    summary: str | None = None
    reasoning: str | None = None
    missing_info: list[str] = Field(default_factory=list, alias="missingInfo")
    follow_up_questions: list[str] = Field(default_factory=list, alias="followUpQuestions")
    source_refs: list[ChartReviewCitationResponse] = Field(default_factory=list, alias="sourceRefs")
    confidence: ChartReviewConfidence | None = None
    review_flags: list[str] = Field(default_factory=list, alias="reviewFlags")
    failure_message: str | None = Field(None, alias="failureMessage")
