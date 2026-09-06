"""Business operations for patient-owned diagnostic reports."""

from uuid import UUID

from app.models.clinical import (
    DiagnosticReportBundleCreate,
    DiagnosticReportResponse,
    ObservationResponse,
)
from app.repositories.diagnostic_report_repository import DiagnosticReportRepository


class DiagnosticReportService:
    def __init__(self, repository: DiagnosticReportRepository):
        self.repository = repository

    async def create(self, bundle: DiagnosticReportBundleCreate) -> DiagnosticReportResponse:
        report = await self.repository.create(bundle)
        await self.repository.session.commit()
        return self._to_response(report)

    async def get_by_id(self, report_id: UUID) -> DiagnosticReportResponse | None:
        report = await self.repository.get_by_id(report_id)
        if report is None:
            return None
        return self._to_response(report)

    async def list_by_patient_id(self, patient_id: UUID) -> list[DiagnosticReportResponse]:
        reports = await self.repository.list_by_patient_id(patient_id)
        return [self._to_response(report) for report in reports]

    @staticmethod
    def _to_response(report) -> DiagnosticReportResponse:
        return DiagnosticReportResponse(
            id=report.id,
            patientId=report.patient_id,
            status=report.status,
            title=report.title,
            effectiveAt=report.effective_at,
            issuedAt=report.issued_at,
            receivedAt=report.received_at,
            conclusion=report.conclusion,
            originatingEncounterId=report.originating_encounter_id,
            createdAt=report.created_at,
            observations=[
                ObservationResponse(
                    id=observation.id,
                    patientId=observation.patient_id,
                    status=observation.status,
                    code=observation.code,
                    display=observation.display,
                    valueType=observation.value_type,
                    value=observation.value,
                    unit=observation.unit,
                    dataAbsentReason=observation.data_absent_reason,
                    effectiveAt=observation.effective_at,
                    diagnosticReportId=observation.diagnostic_report_id,
                    createdAt=observation.created_at,
                )
                for observation in report.observations
            ],
        )
