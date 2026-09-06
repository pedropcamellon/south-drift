"""Persistence operations for diagnostic reports and their observations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.clinical import DiagnosticReportBundleCreate, ResourceType
from app.models.db import DiagnosticReport, Observation
from app.repositories.clinical_provenance_repository import ClinicalProvenanceRepository


class DiagnosticReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, bundle: DiagnosticReportBundleCreate) -> DiagnosticReport:
        report_data = bundle.report.model_dump(exclude={"provenance"})
        report_data["originating_encounter_id"] = report_data.pop("originating_encounter_id")
        report = DiagnosticReport(**report_data)
        self.session.add(report)
        await self.session.flush()
        provenance_repository = ClinicalProvenanceRepository(self.session)
        await provenance_repository.create(
            ResourceType.DIAGNOSTIC_REPORT, report.id, bundle.report.provenance
        )

        for observation_input in bundle.observations:
            observation_data = observation_input.model_dump(exclude={"provenance"})
            observation_data["diagnostic_report_id"] = report.id
            observation = Observation(**observation_data)
            self.session.add(observation)
            await self.session.flush()
            await provenance_repository.create(
                ResourceType.OBSERVATION, observation.id, observation_input.provenance
            )

        await self.session.flush()
        result = await self.session.execute(
            select(DiagnosticReport)
            .where(DiagnosticReport.id == report.id)
            .options(selectinload(DiagnosticReport.observations))
        )
        return result.scalar_one()

    async def get_by_id(self, report_id: UUID) -> DiagnosticReport | None:
        result = await self.session.execute(
            select(DiagnosticReport)
            .where(DiagnosticReport.id == report_id)
            .options(selectinload(DiagnosticReport.observations))
        )
        return result.scalar_one_or_none()

    async def list_by_patient_id(self, patient_id: UUID) -> list[DiagnosticReport]:
        result = await self.session.execute(
            select(DiagnosticReport)
            .where(DiagnosticReport.patient_id == patient_id)
            .options(selectinload(DiagnosticReport.observations))
            .order_by(DiagnosticReport.effective_at.desc(), DiagnosticReport.created_at.desc())
        )
        return list(result.scalars().unique())
