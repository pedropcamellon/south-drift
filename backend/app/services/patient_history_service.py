"""Build read-only patient-history projections from typed clinical records."""

import base64
import binascii
import json
from datetime import datetime
from uuid import UUID

from app.models.clinical import DiagnosticReportResponse, ImagingStudyResponse
from app.models.patient_history import (
    DiagnosticReportTimelineEntry,
    EncounterTimelineEntry,
    ImagingStudyTimelineEntry,
    PatientTimelineEntry,
    PatientTimelineResponse,
)
from app.services.diagnostic_report_service import DiagnosticReportService
from app.services.encounter_service import EncounterService
from app.services.imaging_study_service import ImagingStudyService


class PatientHistoryService:
    def __init__(
        self,
        encounter_service: EncounterService,
        diagnostic_report_service: DiagnosticReportService,
        imaging_study_service: ImagingStudyService,
    ):
        self.encounter_service = encounter_service
        self.diagnostic_report_service = diagnostic_report_service
        self.imaging_study_service = imaging_study_service

    async def get_timeline(
        self, patient_id: UUID, limit: int, cursor: str | None = None
    ) -> PatientTimelineResponse:
        encounters = await self.encounter_service.list_by_patient_id(patient_id)
        reports = await self.diagnostic_report_service.list_by_patient_id(patient_id)
        studies = await self.imaging_study_service.list_by_patient_id(patient_id)
        entries: list[PatientTimelineEntry] = [
            EncounterTimelineEntry(
                id=encounter.id,
                kind="encounter",
                patientId=encounter.patient_id,
                occurredAt=encounter.started_at,
                title=encounter.title,
                status=encounter.status.value,
                encounter=encounter,
            )
            for encounter in encounters
        ]
        entries.extend(self._report_entry(report) for report in reports)
        entries.extend(self._study_entry(study) for study in studies)
        sorted_entries = sorted(entries, key=self._sort_key, reverse=True)
        if cursor is not None:
            cursor_key = self._decode_cursor(cursor)
            sorted_entries = [
                entry for entry in sorted_entries if self._sort_key(entry) < cursor_key
            ]
        page = sorted_entries[:limit]
        next_cursor = self._encode_cursor(page[-1]) if len(sorted_entries) > len(page) else None
        return PatientTimelineResponse(entries=page, nextCursor=next_cursor)

    @staticmethod
    def _report_entry(report: DiagnosticReportResponse) -> DiagnosticReportTimelineEntry:
        return DiagnosticReportTimelineEntry(
            id=report.id,
            kind="diagnostic_report",
            patientId=report.patient_id,
            occurredAt=(
                report.effective_at or report.issued_at or report.received_at or report.created_at
            ),
            title=report.title,
            status=report.status.value,
            diagnosticReport=report,
        )

    @staticmethod
    def _study_entry(study: ImagingStudyResponse) -> ImagingStudyTimelineEntry:
        return ImagingStudyTimelineEntry(
            id=study.id,
            kind="imaging_study",
            patientId=study.patient_id,
            occurredAt=study.performed_at,
            title=f"{study.modality.value.upper()} imaging study",
            status="completed",
            imagingStudy=study,
        )

    @staticmethod
    def _sort_key(entry: PatientTimelineEntry) -> tuple[datetime, str, str]:
        return (entry.occurred_at, entry.kind, str(entry.id))

    @classmethod
    def _encode_cursor(cls, entry: PatientTimelineEntry) -> str:
        occurred_at, kind, entry_id = cls._sort_key(entry)
        cursor = json.dumps([occurred_at.isoformat(), kind, entry_id], separators=(",", ":"))
        return base64.urlsafe_b64encode(cursor.encode()).decode()

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[datetime, str, str]:
        try:
            occurred_at, kind, entry_id = json.loads(base64.urlsafe_b64decode(cursor))
            return (datetime.fromisoformat(occurred_at), kind, entry_id)
        except (ValueError, TypeError, binascii.Error, json.JSONDecodeError) as error:
            raise ValueError("Invalid patient timeline cursor") from error
