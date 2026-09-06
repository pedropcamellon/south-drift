"""Contracts for validated summarization service responses."""

from pydantic import BaseModel, Field


class StructuredSummary(BaseModel):
    chief_complaint: str | None = Field(None, alias="chief_complaint")
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    clinical_tags: list[str] = Field(default_factory=list, alias="clinical_tags")
    icd_codes: list[str] = Field(default_factory=list, alias="icd_codes")
    action_items: list[str] = Field(default_factory=list, alias="action_items")


class SummarizationResponse(BaseModel):
    summary: str
    structured_data: StructuredSummary
    processing_time: float
    model_used: str
    provider: str
