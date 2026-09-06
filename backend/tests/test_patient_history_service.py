from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.clinical import (
    DiagnosticReportResponse,
    DiagnosticReportStatus,
    EncounterPurpose,
    EncounterResponse,
    EncounterStatus,
    EncounterType,
    ImagingModality,
    ImagingStudyResponse,
)
from app.services.patient_history_service import PatientHistoryService


class EncounterServiceStub:
    def __init__(self, encounters: list[EncounterResponse]):
        self.encounters = encounters

    async def list_by_patient_id(self, _: object) -> list[EncounterResponse]:
        return self.encounters


class DiagnosticReportServiceStub:
    def __init__(self, reports: list[DiagnosticReportResponse]):
        self.reports = reports

    async def list_by_patient_id(self, _: object) -> list[DiagnosticReportResponse]:
        return self.reports


class ImagingStudyServiceStub:
    def __init__(self, studies: list[ImagingStudyResponse]):
        self.studies = studies

    async def list_by_patient_id(self, _: object) -> list[ImagingStudyResponse]:
        return self.studies


@pytest.mark.asyncio
async def test_timeline_merges_native_records_with_report_timestamp_fallback() -> None:
    patient_id = uuid4()
    encounter_time = datetime(2026, 9, 3, tzinfo=UTC)
    report_created_at = encounter_time + timedelta(days=1)
    encounter = EncounterResponse(
        id=uuid4(),
        patientId=patient_id,
        encounterType=EncounterType.OUTPATIENT,
        purpose=EncounterPurpose.FOLLOW_UP,
        status=EncounterStatus.COMPLETED,
        title="Follow-up",
        startedAt=encounter_time,
        createdAt=encounter_time,
    )
    report = DiagnosticReportResponse(
        id=uuid4(),
        patientId=patient_id,
        status=DiagnosticReportStatus.FINAL,
        title="Laboratory panel",
        createdAt=report_created_at,
    )
    imaging_study = ImagingStudyResponse(
        id=uuid4(),
        patientId=patient_id,
        modality=ImagingModality.XRAY,
        performedAt=report_created_at + timedelta(days=1),
        createdAt=report_created_at + timedelta(days=1),
    )
    service = PatientHistoryService(
        EncounterServiceStub([encounter]),
        DiagnosticReportServiceStub([report]),
        ImagingStudyServiceStub([imaging_study]),
    )

    timeline = await service.get_timeline(patient_id, limit=50)

    assert [entry.kind for entry in timeline.entries] == [
        "imaging_study",
        "diagnostic_report",
        "encounter",
    ]
    assert timeline.entries[0].occurred_at == imaging_study.performed_at
    assert timeline.entries[1].occurred_at == report_created_at
    assert timeline.entries[2].occurred_at == encounter_time


@pytest.mark.asyncio
async def test_timeline_cursor_returns_the_next_chronological_page() -> None:
    patient_id = uuid4()
    base_time = datetime(2026, 9, 1, tzinfo=UTC)
    encounters = [
        EncounterResponse(
            id=uuid4(),
            patientId=patient_id,
            encounterType=EncounterType.OUTPATIENT,
            purpose=EncounterPurpose.FOLLOW_UP,
            status=EncounterStatus.COMPLETED,
            title=f"Follow-up {index}",
            startedAt=base_time + timedelta(days=index),
            createdAt=base_time + timedelta(days=index),
        )
        for index in range(3)
    ]
    service = PatientHistoryService(
        EncounterServiceStub(encounters),
        DiagnosticReportServiceStub([]),
        ImagingStudyServiceStub([]),
    )

    first_page = await service.get_timeline(patient_id, limit=2)
    second_page = await service.get_timeline(patient_id, limit=2, cursor=first_page.next_cursor)

    assert len(first_page.entries) == 2
    assert first_page.next_cursor is not None
    assert [entry.title for entry in second_page.entries] == ["Follow-up 0"]
