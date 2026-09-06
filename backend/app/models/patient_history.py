"""Read-model contracts for a patient's chronological clinical history."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.clinical import (
    DiagnosticReportResponse,
    EncounterResponse,
    ImagingStudyResponse,
)


class EncounterTimelineEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    kind: Literal["encounter"]
    patient_id: UUID = Field(..., alias="patientId")
    occurred_at: datetime = Field(..., alias="occurredAt")
    title: str
    status: str
    encounter: EncounterResponse


class DiagnosticReportTimelineEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    kind: Literal["diagnostic_report"]
    patient_id: UUID = Field(..., alias="patientId")
    occurred_at: datetime = Field(..., alias="occurredAt")
    title: str
    status: str
    diagnostic_report: DiagnosticReportResponse = Field(..., alias="diagnosticReport")


class ImagingStudyTimelineEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    kind: Literal["imaging_study"]
    patient_id: UUID = Field(..., alias="patientId")
    occurred_at: datetime = Field(..., alias="occurredAt")
    title: str
    status: str
    imaging_study: ImagingStudyResponse = Field(..., alias="imagingStudy")


PatientTimelineEntry = (
    EncounterTimelineEntry | DiagnosticReportTimelineEntry | ImagingStudyTimelineEntry
)


class PatientTimelineResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    entries: list[PatientTimelineEntry]
    next_cursor: str | None = Field(None, alias="nextCursor")
