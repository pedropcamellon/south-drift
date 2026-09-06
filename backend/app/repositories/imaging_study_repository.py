"""Persistence operations for patient-owned imaging studies."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PatientNotFoundError
from app.models.clinical import ImagingStudyCreate, ResourceType
from app.models.db import ClinicalDocument, DiagnosticReport, Encounter, ImagingStudy, Patient
from app.repositories.clinical_provenance_repository import ClinicalProvenanceRepository


class ImagingStudyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_patient_id(self, patient_id: UUID) -> list[ImagingStudy]:
        result = await self.session.execute(
            select(ImagingStudy)
            .where(ImagingStudy.patient_id == patient_id)
            .order_by(ImagingStudy.performed_at.desc(), ImagingStudy.created_at.desc())
        )
        return list(result.scalars())

    async def get_by_id(self, study_id: UUID) -> ImagingStudy | None:
        return await self.session.scalar(select(ImagingStudy).where(ImagingStudy.id == study_id))

    async def create(self, study_input: ImagingStudyCreate) -> ImagingStudy:
        await self._require_patient(study_input.patient_id)
        await self._require_same_patient_reference(
            Encounter, study_input.originating_encounter_id, study_input.patient_id, "encounter"
        )
        await self._require_same_patient_reference(
            ClinicalDocument,
            study_input.clinical_document_id,
            study_input.patient_id,
            "clinical document",
        )
        await self._require_same_patient_reference(
            DiagnosticReport,
            study_input.diagnostic_report_id,
            study_input.patient_id,
            "diagnostic report",
        )
        study_data = study_input.model_dump(exclude={"provenance"})
        study_data["modality"] = study_input.modality.value
        study = ImagingStudy(**study_data)
        self.session.add(study)
        await self.session.flush()
        await ClinicalProvenanceRepository(self.session).create(
            ResourceType.IMAGING_STUDY, study.id, study_input.provenance
        )
        return study

    async def _require_patient(self, patient_id: UUID) -> None:
        patient = await self.session.scalar(select(Patient.id).where(Patient.id == patient_id))
        if patient is None:
            raise PatientNotFoundError(str(patient_id))

    async def _require_same_patient_reference(
        self,
        model: type[Encounter] | type[ClinicalDocument] | type[DiagnosticReport],
        resource_id: UUID | None,
        patient_id: UUID,
        resource_name: str,
    ) -> None:
        if resource_id is None:
            return
        reference = await self.session.scalar(
            select(model.id).where(model.id == resource_id, model.patient_id == patient_id)
        )
        if reference is None:
            raise ValueError(f"Imaging {resource_name} must belong to the imaging patient")
