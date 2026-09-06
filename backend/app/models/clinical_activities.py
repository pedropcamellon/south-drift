"""Contracts for independently dated patient clinical activities."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.clinical import ProvenanceInput


class ImmunizationStatus(StrEnum):
    COMPLETED = "completed"
    NOT_DONE = "not_done"
    ENTERED_IN_ERROR = "entered_in_error"


class MedicationStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STOPPED = "stopped"
    ENTERED_IN_ERROR = "entered_in_error"


class ProcedureStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered_in_error"


class ImmunizationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: UUID = Field(..., alias="patientId")
    status: ImmunizationStatus
    vaccine_code: str = Field(..., min_length=1, max_length=100, alias="vaccineCode")
    vaccine_display: str = Field(..., min_length=1, max_length=200, alias="vaccineDisplay")
    administered_at: datetime = Field(..., alias="administeredAt")
    manufacturer: str | None = Field(None, min_length=1, max_length=200)
    lot_number: str | None = Field(None, min_length=1, max_length=100, alias="lotNumber")
    performer_name: str | None = Field(None, min_length=1, max_length=200, alias="performerName")
    recorded_at: datetime | None = Field(None, alias="recordedAt")
    originating_encounter_id: UUID | None = Field(None, alias="originatingEncounterId")
    provenance: ProvenanceInput | None = None


class ImmunizationResponse(ImmunizationCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    created_at: datetime = Field(..., alias="createdAt")


class MedicationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: UUID = Field(..., alias="patientId")
    status: MedicationStatus
    medication_code: str = Field(..., min_length=1, max_length=100, alias="medicationCode")
    medication_display: str = Field(..., min_length=1, max_length=200, alias="medicationDisplay")
    dosage_text: str | None = Field(None, min_length=1, max_length=2_000, alias="dosageText")
    prescribed_at: datetime | None = Field(None, alias="prescribedAt")
    started_at: datetime | None = Field(None, alias="startedAt")
    ended_at: datetime | None = Field(None, alias="endedAt")
    recorded_at: datetime | None = Field(None, alias="recordedAt")
    originating_encounter_id: UUID | None = Field(None, alias="originatingEncounterId")
    provenance: ProvenanceInput | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "MedicationCreate":
        if (
            self.ended_at is not None
            and self.started_at is not None
            and self.ended_at < self.started_at
        ):
            raise ValueError("Medication end time must not be before its start time")
        return self


class MedicationResponse(MedicationCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    created_at: datetime = Field(..., alias="createdAt")


class ProcedureCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: UUID = Field(..., alias="patientId")
    status: ProcedureStatus
    code: str = Field(..., min_length=1, max_length=100)
    display: str = Field(..., min_length=1, max_length=200)
    performed_at: datetime = Field(..., alias="performedAt")
    performer_name: str | None = Field(None, min_length=1, max_length=200, alias="performerName")
    details: dict[str, object] | None = None
    recorded_at: datetime | None = Field(None, alias="recordedAt")
    originating_encounter_id: UUID | None = Field(None, alias="originatingEncounterId")
    provenance: ProvenanceInput | None = None


class ProcedureResponse(ProcedureCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    created_at: datetime = Field(..., alias="createdAt")
