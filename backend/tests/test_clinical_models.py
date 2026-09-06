from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Table
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical import (
    AttachmentCreate,
    ClinicalDocumentBundleCreate,
    ClinicalDocumentCategory,
    ClinicalDocumentCreate,
    ClinicalRecordStatus,
    DiagnosticReportBundleCreate,
    DiagnosticReportCreate,
    DiagnosticReportStatus,
    EncounterCreate,
    EncounterNarrativeResponse,
    EncounterPurpose,
    EncounterStatus,
    EncounterType,
    ImagingStudyCreate,
    ObservationCreate,
    ObservationStatus,
    ObservationValueType,
    ProvenanceInput,
    ResourceRelationshipCreate,
    ResourceRelationshipType,
    ResourceType,
)
from app.models.clinical_activities import (
    ImmunizationCreate,
    ImmunizationStatus,
    MedicationCreate,
    MedicationStatus,
    ProcedureCreate,
    ProcedureStatus,
)
from app.models.db import (
    Attachment,
    ClinicalProvenance,
    Encounter,
    ImagingStudy,
    Immunization,
    Medication,
    Observation,
    Procedure,
)
from app.repositories.clinical_provenance_repository import ClinicalProvenanceRepository


def test_encounter_rejects_end_before_start() -> None:
    started_at = datetime.now(UTC)

    with pytest.raises(ValidationError, match="end time"):
        EncounterCreate(
            patientId=uuid4(),
            encounterType=EncounterType.OUTPATIENT,
            purpose=EncounterPurpose.FOLLOW_UP,
            status=EncounterStatus.COMPLETED,
            title="Follow-up",
            startedAt=started_at,
            endedAt=started_at - timedelta(minutes=1),
        )


def test_clinical_document_bundle_keeps_storage_metadata_on_attachment() -> None:
    patient_id = uuid4()
    document = ClinicalDocumentCreate(
        patientId=patient_id,
        category=ClinicalDocumentCategory.EXTERNAL_RECORD,
        status=ClinicalRecordStatus.FINAL,
        title="Synthetic external record",
    )
    attachment = AttachmentCreate(
        storageKey="documents/synthetic/external-record.pdf",
        fileName="external-record.pdf",
        mimeType="application/pdf",
        byteSize=512,
    )

    bundle = ClinicalDocumentBundleCreate(document=document, attachments=[attachment])

    assert bundle.document.patient_id == patient_id
    assert bundle.attachments[0].storage_key == "documents/synthetic/external-record.pdf"


def test_encounter_narrative_response_includes_derived_patient_ownership() -> None:
    patient_id = uuid4()
    encounter_id = uuid4()

    narrative = EncounterNarrativeResponse(
        id=uuid4(),
        patientId=patient_id,
        encounterId=encounter_id,
        content="Synthetic encounter narrative.",
        status="final",
        createdAt=datetime.now(UTC),
    )

    assert narrative.patient_id == patient_id
    assert narrative.encounter_id == encounter_id


def test_observation_requires_value_or_absent_reason() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        ObservationCreate(
            patientId=uuid4(),
            status=ObservationStatus.FINAL,
            code="example-code",
            display="Example result",
            valueType=ObservationValueType.TEXT,
        )


def test_database_tables_match_clinical_time_and_value_invariants() -> None:
    encounter_table = cast(Table, Encounter.__table__)
    observation_table = cast(Table, Observation.__table__)
    encounter_constraints = {
        constraint.name
        for constraint in encounter_table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    observation_constraints = {
        constraint.name
        for constraint in observation_table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_encounter_time_range" in encounter_constraints
    assert "ck_observation_value_or_absence_reason" in observation_constraints


def test_attachment_and_imaging_study_keep_explicit_typed_relationships() -> None:
    attachment_table = cast(Table, Attachment.__table__)
    imaging_study_table = cast(Table, ImagingStudy.__table__)
    attachment_foreign_keys = {
        foreign_key.target_fullname: foreign_key.ondelete
        for constraint in attachment_table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        for foreign_key in constraint.elements
    }
    imaging_foreign_keys = {
        foreign_key.target_fullname: foreign_key.ondelete
        for constraint in imaging_study_table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        for foreign_key in constraint.elements
    }

    assert attachment_foreign_keys["clinical_document.id"] == "CASCADE"
    assert imaging_foreign_keys["clinical_document.id"] == "SET NULL"


def test_imaging_study_accepts_an_optional_source_document() -> None:
    source_document_id = uuid4()

    study = ImagingStudyCreate(
        patientId=uuid4(),
        modality="xray",
        performedAt=datetime(2026, 9, 1, tzinfo=UTC),
        clinicalDocumentId=source_document_id,
    )

    assert study.clinical_document_id == source_document_id


def test_typed_activity_contracts_keep_independent_dates_and_encounter_context() -> None:
    patient_id = uuid4()
    encounter_id = uuid4()
    occurred_at = datetime(2026, 9, 1, tzinfo=UTC)

    immunization = ImmunizationCreate(
        patientId=patient_id,
        originatingEncounterId=encounter_id,
        status=ImmunizationStatus.COMPLETED,
        vaccineCode="influenza",
        vaccineDisplay="Influenza vaccine",
        administeredAt=occurred_at,
        lotNumber="synthetic-lot",
    )
    medication = MedicationCreate(
        patientId=patient_id,
        originatingEncounterId=encounter_id,
        status=MedicationStatus.ACTIVE,
        medicationCode="example-medication",
        medicationDisplay="Example medication",
        startedAt=occurred_at,
    )
    procedure = ProcedureCreate(
        patientId=patient_id,
        originatingEncounterId=encounter_id,
        status=ProcedureStatus.COMPLETED,
        code="example-procedure",
        display="Example procedure",
        performedAt=occurred_at,
    )

    assert immunization.administered_at == occurred_at
    assert medication.started_at == occurred_at
    assert procedure.performed_at == occurred_at
    assert immunization.originating_encounter_id == encounter_id
    assert medication.originating_encounter_id == encounter_id
    assert procedure.originating_encounter_id == encounter_id


def test_medication_rejects_an_end_before_its_start() -> None:
    started_at = datetime.now(UTC)

    with pytest.raises(ValidationError, match="Medication end time"):
        MedicationCreate(
            patientId=uuid4(),
            status=MedicationStatus.STOPPED,
            medicationCode="example-medication",
            medicationDisplay="Example medication",
            startedAt=started_at,
            endedAt=started_at - timedelta(minutes=1),
        )


def test_typed_activity_tables_have_patient_and_encounter_foreign_keys() -> None:
    tables = [
        cast(Table, Immunization.__table__),
        cast(Table, Medication.__table__),
        cast(Table, Procedure.__table__),
    ]

    for table in tables:
        foreign_keys = {
            foreign_key.target_fullname: foreign_key.ondelete
            for constraint in table.constraints
            if isinstance(constraint, ForeignKeyConstraint)
            for foreign_key in constraint.elements
        }
        assert foreign_keys["patient.id"] == "CASCADE"
        assert foreign_keys["encounter.id"] == "SET NULL"


@pytest.mark.asyncio
async def test_provenance_repository_persists_validated_source_version() -> None:
    class Session:
        def __init__(self) -> None:
            self.records: list[object] = []

        def add(self, record: object) -> None:
            self.records.append(record)

        async def flush(self) -> None:
            return

    session = Session()
    resource_id = uuid4()
    provenance = ProvenanceInput(
        sourceSystem="synthetic-lab",
        externalId="panel-001",
        version="2",
        recordedAt=datetime(2026, 9, 1, tzinfo=UTC),
    )

    await ClinicalProvenanceRepository(cast(AsyncSession, session)).create(
        ResourceType.DIAGNOSTIC_REPORT, resource_id, provenance
    )

    assert len(session.records) == 1
    row = session.records[0]
    assert isinstance(row, ClinicalProvenance)
    assert row.resource_type == ResourceType.DIAGNOSTIC_REPORT.value
    assert row.resource_id == resource_id
    assert row.external_id == "panel-001"
    assert row.version == "2"


def test_report_and_observation_keep_independent_effective_times() -> None:
    patient_id = uuid4()
    report = DiagnosticReportCreate(
        patientId=patient_id,
        status=DiagnosticReportStatus.FINAL,
        title="Respiratory panel",
        effectiveAt=datetime(2026, 9, 1, tzinfo=UTC),
        issuedAt=datetime(2026, 9, 2, tzinfo=UTC),
    )
    observation = ObservationCreate(
        patientId=patient_id,
        status=ObservationStatus.FINAL,
        code="respiratory-virus",
        display="Respiratory virus result",
        valueType=ObservationValueType.TEXT,
        value="not detected",
        effectiveAt=datetime(2026, 9, 1, tzinfo=UTC),
    )

    assert report.issued_at is not None
    assert observation.effective_at is not None
    assert report.issued_at > observation.effective_at
    assert "diagnostic_report_id" not in observation.model_fields_set


def test_resource_relationship_rejects_self_reference() -> None:
    resource_id = uuid4()

    with pytest.raises(ValidationError, match="cannot target itself"):
        ResourceRelationshipCreate(
            sourceResourceType=ResourceType.CLINICAL_DOCUMENT,
            sourceResourceId=resource_id,
            targetResourceType=ResourceType.CLINICAL_DOCUMENT,
            targetResourceId=resource_id,
            relationshipType=ResourceRelationshipType.HAS_ATTACHMENT,
        )


def test_report_bundle_rejects_observation_for_another_patient() -> None:
    report_patient_id = uuid4()
    report = DiagnosticReportCreate(
        patientId=report_patient_id,
        status=DiagnosticReportStatus.FINAL,
        title="Respiratory panel",
    )
    observation = ObservationCreate(
        patientId=uuid4(),
        status=ObservationStatus.FINAL,
        code="respiratory-virus",
        display="Respiratory virus result",
        valueType=ObservationValueType.TEXT,
        value="not detected",
    )

    with pytest.raises(ValidationError, match="report patient"):
        DiagnosticReportBundleCreate(report=report, observations=[observation])
