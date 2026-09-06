"""Clinical record contracts independent from storage and downstream consumers."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EncounterType(StrEnum):
    OUTPATIENT = "outpatient"
    TELEHEALTH = "telehealth"
    TELEPHONE = "telephone"
    PORTAL = "portal"
    EMERGENCY = "emergency"
    INPATIENT = "inpatient"


class EncounterPurpose(StrEnum):
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    PREVENTIVE = "preventive"
    PROCEDURE = "procedure"


class EncounterStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TranscriptionStatus(StrEnum):
    PROCESSING = "processing"
    TRANSCRIBED = "transcribed"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class VoiceNoteWorkflowMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    workflow_id: str | None = Field(None, alias="workflowId")
    run_id: str | None = Field(None, alias="runId")
    status: TranscriptionStatus | None = None
    failure_stage: str | None = Field(None, alias="failureStage")
    error_message: str | None = Field(None, alias="errorMessage")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    transcript_applied_at: datetime | None = Field(None, alias="transcriptAppliedAt")


class EncounterAudioMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    filename: str | None = None
    storage_key: str | None = Field(None, alias="storageKey")
    storage_url: str | None = Field(None, alias="storageUrl")
    size: int | None = None
    content_type: str | None = Field(None, alias="contentType")
    transcription_status: TranscriptionStatus | None = Field(None, alias="transcriptionStatus")
    workflow: VoiceNoteWorkflowMetadata | None = Field(None, alias="voiceNoteWorkflow")


class ClinicalDocumentCategory(StrEnum):
    CLINICAL_NOTE = "clinical_note"
    EXTERNAL_RECORD = "external_record"
    VISIT_SUMMARY = "visit_summary"
    PATIENT_SUBMISSION = "patient_submission"


class ClinicalRecordStatus(StrEnum):
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    ENTERED_IN_ERROR = "entered_in_error"


class DiagnosticReportStatus(StrEnum):
    REGISTERED = "registered"
    PARTIAL = "partial"
    FINAL = "final"
    AMENDED = "amended"
    CANCELLED = "cancelled"


class ObservationStatus(StrEnum):
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CANCELLED = "cancelled"


class ImagingModality(StrEnum):
    XRAY = "xray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"


class ResourceType(StrEnum):
    ENCOUNTER = "encounter"
    ENCOUNTER_NARRATIVE = "encounter_narrative"
    CLINICAL_DOCUMENT = "clinical_document"
    ATTACHMENT = "attachment"
    DIAGNOSTIC_REPORT = "diagnostic_report"
    OBSERVATION = "observation"
    IMAGING_STUDY = "imaging_study"
    IMMUNIZATION = "immunization"
    MEDICATION = "medication"
    PROCEDURE = "procedure"


class ResourceRelationshipType(StrEnum):
    ORIGINATED_DURING = "originated_during"
    HAS_ATTACHMENT = "has_attachment"
    HAS_RESULT = "has_result"
    DOCUMENTS = "documents"
    DERIVED_FROM = "derived_from"


class ProvenanceInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_system: str | None = Field(None, min_length=1, max_length=100, alias="sourceSystem")
    external_id: str | None = Field(None, min_length=1, max_length=200, alias="externalId")
    authored_at: datetime | None = Field(None, alias="authoredAt")
    received_at: datetime | None = Field(None, alias="receivedAt")
    recorded_at: datetime | None = Field(None, alias="recordedAt")
    author_id: str | None = Field(None, min_length=1, max_length=100, alias="authorId")
    recorder_id: str | None = Field(None, min_length=1, max_length=100, alias="recorderId")
    version: str | None = Field(None, min_length=1, max_length=100)


class EncounterBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: UUID = Field(..., alias="patientId")
    encounter_type: EncounterType = Field(..., alias="encounterType")
    purpose: EncounterPurpose
    status: EncounterStatus
    title: str = Field(..., min_length=1, max_length=200)
    started_at: datetime = Field(..., alias="startedAt")
    ended_at: datetime | None = Field(None, alias="endedAt")
    location: str | None = Field(None, min_length=1, max_length=200)
    clinician_id: str | None = Field(None, min_length=1, max_length=100, alias="clinicianId")
    clinician_name: str | None = Field(None, min_length=1, max_length=200, alias="clinicianName")
    description: str | None = Field(None, min_length=1, max_length=20_000)
    summary: str | None = Field(None, min_length=1, max_length=20_000)
    audio_metadata: EncounterAudioMetadata | None = Field(None, alias="audioMetadata")
    structured_summary: dict[str, object] | None = Field(None, alias="structuredSummary")
    chief_complaint: str | None = Field(
        None, min_length=1, max_length=10_000, alias="chiefComplaint"
    )
    clinical_assessment: str | None = Field(
        None, min_length=1, max_length=10_000, alias="clinicalAssessment"
    )
    treatment_plan: str | None = Field(None, min_length=1, max_length=10_000, alias="treatmentPlan")
    is_compliant: bool = Field(True, alias="isCompliant")
    created_by: str = Field("system", min_length=1, max_length=100, alias="createdBy")
    updated_by: str | None = Field(None, min_length=1, max_length=100, alias="updatedBy")
    prior_encounter_id: UUID | None = Field(None, alias="priorEncounterId")
    provenance: ProvenanceInput | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "EncounterBase":
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("Encounter end time must not be before its start time")
        return self


class EncounterCreate(EncounterBase):
    pass


class EncounterUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    encounter_type: EncounterType | None = Field(None, alias="encounterType")
    purpose: EncounterPurpose | None = None
    status: EncounterStatus | None = None
    title: str | None = Field(None, min_length=1, max_length=200)
    started_at: datetime | None = Field(None, alias="startedAt")
    ended_at: datetime | None = Field(None, alias="endedAt")
    location: str | None = Field(None, min_length=1, max_length=200)
    clinician_id: str | None = Field(None, min_length=1, max_length=100, alias="clinicianId")
    clinician_name: str | None = Field(None, min_length=1, max_length=200, alias="clinicianName")
    description: str | None = Field(None, min_length=1, max_length=20_000)
    summary: str | None = Field(None, min_length=1, max_length=20_000)
    audio_metadata: EncounterAudioMetadata | None = Field(None, alias="audioMetadata")
    structured_summary: dict[str, object] | None = Field(None, alias="structuredSummary")
    chief_complaint: str | None = Field(
        None, min_length=1, max_length=10_000, alias="chiefComplaint"
    )
    clinical_assessment: str | None = Field(
        None, min_length=1, max_length=10_000, alias="clinicalAssessment"
    )
    treatment_plan: str | None = Field(None, min_length=1, max_length=10_000, alias="treatmentPlan")
    is_compliant: bool | None = Field(None, alias="isCompliant")
    updated_by: str | None = Field(None, min_length=1, max_length=100, alias="updatedBy")


class EncounterNarrativeCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    encounter_id: UUID = Field(..., alias="encounterId")
    content: str = Field(..., min_length=1, max_length=20_000)
    status: ClinicalRecordStatus
    provenance: ProvenanceInput | None = None


class EncounterNarrativeResponse(EncounterNarrativeCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    patient_id: UUID = Field(..., alias="patientId")
    created_at: datetime = Field(..., alias="createdAt")


class EncounterNarrativeUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(..., min_length=1, max_length=20_000)
    status: ClinicalRecordStatus = ClinicalRecordStatus.PRELIMINARY


class EncounterResponse(EncounterBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    narratives: list[EncounterNarrativeResponse] = Field(default_factory=list)
    note: str | None = None


class VoiceNoteWorkflowStatus(StrEnum):
    IDLE = "idle"
    PROCESSING = "processing"
    TRANSCRIBED = "transcribed"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class VoiceNoteWorkflowStartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    encounter_id: UUID = Field(..., alias="encounterId")
    status: VoiceNoteWorkflowStatus = VoiceNoteWorkflowStatus.PROCESSING
    workflow_id: str = Field(..., alias="workflowId")
    run_id: str = Field(..., alias="runId")
    message: str


class VoiceNoteUploadResponse(VoiceNoteWorkflowStartResponse):
    filename: str | None = None
    storage_key: str = Field(..., alias="storageKey")
    storage_url: str = Field(..., alias="storageUrl")
    size: int = Field(..., ge=0)


class VoiceNoteWorkflowStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    encounter_id: UUID = Field(..., alias="encounterId")
    workflow_id: str | None = Field(None, alias="workflowId")
    run_id: str | None = Field(None, alias="runId")
    status: VoiceNoteWorkflowStatus
    failure_stage: str | None = Field(None, alias="failureStage")
    error_message: str | None = Field(None, alias="errorMessage")
    encounter: EncounterResponse


class ClinicalDocumentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: UUID = Field(..., alias="patientId")
    category: ClinicalDocumentCategory
    status: ClinicalRecordStatus
    title: str = Field(..., min_length=1, max_length=200)
    authored_at: datetime | None = Field(None, alias="authoredAt")
    received_at: datetime | None = Field(None, alias="receivedAt")
    encounter_id: UUID | None = Field(None, alias="encounterId")
    provenance: ProvenanceInput | None = None


class AttachmentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    storage_key: str = Field(..., min_length=1, max_length=500, alias="storageKey")
    file_name: str = Field(..., min_length=1, max_length=255, alias="fileName")
    mime_type: str = Field(..., min_length=1, max_length=100, alias="mimeType")
    byte_size: int = Field(..., ge=0, alias="byteSize")
    checksum: str | None = Field(None, min_length=1, max_length=200)


class ClinicalDocumentBundleCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    document: ClinicalDocumentCreate
    attachments: list[AttachmentCreate] = Field(default_factory=list, max_length=25)


class AttachmentResponse(AttachmentCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    clinical_document_id: UUID = Field(..., alias="clinicalDocumentId")
    created_at: datetime = Field(..., alias="createdAt")


class ClinicalDocumentResponse(ClinicalDocumentCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    created_at: datetime = Field(..., alias="createdAt")
    attachments: list[AttachmentResponse] = Field(default_factory=list)


class ResourceRelationshipCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_resource_type: ResourceType = Field(..., alias="sourceResourceType")
    source_resource_id: UUID = Field(..., alias="sourceResourceId")
    target_resource_type: ResourceType = Field(..., alias="targetResourceType")
    target_resource_id: UUID = Field(..., alias="targetResourceId")
    relationship_type: ResourceRelationshipType = Field(..., alias="relationshipType")

    @model_validator(mode="after")
    def validate_distinct_resources(self) -> "ResourceRelationshipCreate":
        if (
            self.source_resource_type == self.target_resource_type
            and self.source_resource_id == self.target_resource_id
        ):
            raise ValueError("A resource relationship cannot target itself")
        return self


class DiagnosticReportCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: UUID = Field(..., alias="patientId")
    status: DiagnosticReportStatus
    title: str = Field(..., min_length=1, max_length=200)
    effective_at: datetime | None = Field(None, alias="effectiveAt")
    issued_at: datetime | None = Field(None, alias="issuedAt")
    received_at: datetime | None = Field(None, alias="receivedAt")
    conclusion: str | None = Field(None, min_length=1, max_length=10_000)
    originating_encounter_id: UUID | None = Field(None, alias="originatingEncounterId")
    provenance: ProvenanceInput | None = None


class ObservationValueType(StrEnum):
    QUANTITY = "quantity"
    TEXT = "text"
    CODE = "code"
    BOOLEAN = "boolean"


class ObservationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: UUID = Field(..., alias="patientId")
    status: ObservationStatus
    code: str = Field(..., min_length=1, max_length=200)
    display: str = Field(..., min_length=1, max_length=200)
    value_type: ObservationValueType = Field(..., alias="valueType")
    value: str | None = Field(None, min_length=1, max_length=2_000)
    unit: str | None = Field(None, min_length=1, max_length=100)
    data_absent_reason: str | None = Field(
        None, min_length=1, max_length=500, alias="dataAbsentReason"
    )
    effective_at: datetime | None = Field(None, alias="effectiveAt")
    provenance: ProvenanceInput | None = None

    @model_validator(mode="after")
    def validate_value(self) -> "ObservationCreate":
        if (self.value is None) == (self.data_absent_reason is None):
            raise ValueError("Observation requires exactly one of value or data_absent_reason")
        return self


class DiagnosticReportBundleCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    report: DiagnosticReportCreate
    observations: list[ObservationCreate] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_patient_ownership(self) -> "DiagnosticReportBundleCreate":
        if any(
            observation.patient_id != self.report.patient_id for observation in self.observations
        ):
            raise ValueError("Diagnostic report observations must belong to the report patient")
        return self


class ObservationResponse(ObservationCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    diagnostic_report_id: UUID = Field(..., alias="diagnosticReportId")
    created_at: datetime = Field(..., alias="createdAt")


class DiagnosticReportResponse(DiagnosticReportCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    created_at: datetime = Field(..., alias="createdAt")
    observations: list[ObservationResponse] = Field(default_factory=list)


class ImagingStudyCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: UUID = Field(..., alias="patientId")
    modality: ImagingModality
    performed_at: datetime = Field(..., alias="performedAt")
    external_study_id: str | None = Field(
        None, min_length=1, max_length=200, alias="externalStudyId"
    )
    originating_encounter_id: UUID | None = Field(None, alias="originatingEncounterId")
    clinical_document_id: UUID | None = Field(None, alias="clinicalDocumentId")
    diagnostic_report_id: UUID | None = Field(None, alias="diagnosticReportId")
    provenance: ProvenanceInput | None = None


class ImagingStudyResponse(ImagingStudyCreate):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    created_at: datetime = Field(..., alias="createdAt")
