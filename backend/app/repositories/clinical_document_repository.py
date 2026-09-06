"""Persistence operations for clinical documents and their attachments."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import PatientNotFoundError
from app.models.clinical import ClinicalDocumentBundleCreate, ResourceType
from app.models.db import Attachment, ClinicalDocument, Encounter, Patient
from app.repositories.clinical_provenance_repository import ClinicalProvenanceRepository


class ClinicalDocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_patient_id(self, patient_id: UUID) -> list[ClinicalDocument]:
        result = await self.session.execute(
            select(ClinicalDocument)
            .where(ClinicalDocument.patient_id == patient_id)
            .order_by(ClinicalDocument.created_at.desc())
            .options(selectinload(ClinicalDocument.attachments))
        )
        return list(result.scalars())

    async def get_by_id(self, document_id: UUID) -> ClinicalDocument | None:
        result = await self.session.execute(
            select(ClinicalDocument)
            .where(ClinicalDocument.id == document_id)
            .options(selectinload(ClinicalDocument.attachments))
        )
        return result.scalar_one_or_none()

    async def get_attachment(self, document_id: UUID, attachment_id: UUID) -> Attachment | None:
        return await self.session.scalar(
            select(Attachment).where(
                Attachment.id == attachment_id,
                Attachment.clinical_document_id == document_id,
            )
        )

    async def delete(self, document_id: UUID) -> bool:
        document = await self.get_by_id(document_id)
        if document is None:
            return False
        await self.session.delete(document)
        await self.session.flush()
        return True

    async def create(self, bundle: ClinicalDocumentBundleCreate) -> ClinicalDocument:
        document_input = bundle.document
        await self._require_patient(document_input.patient_id)
        if document_input.encounter_id is not None:
            await self._require_patient_encounter(
                document_input.encounter_id, document_input.patient_id
            )

        document_data = document_input.model_dump(exclude={"provenance"})
        document_data["category"] = document_input.category.value
        document_data["status"] = document_input.status.value
        document = ClinicalDocument(**document_data)
        self.session.add(document)
        await self.session.flush()
        await ClinicalProvenanceRepository(self.session).create(
            ResourceType.CLINICAL_DOCUMENT, document.id, document_input.provenance
        )

        self.session.add_all(
            [
                Attachment(clinical_document_id=document.id, **attachment.model_dump())
                for attachment in bundle.attachments
            ]
        )
        await self.session.flush()
        created_document = await self.get_by_id(document.id)
        if created_document is None:
            raise RuntimeError("Created clinical document could not be reloaded")
        return created_document

    async def _require_patient(self, patient_id: UUID) -> None:
        patient = await self.session.scalar(select(Patient.id).where(Patient.id == patient_id))
        if patient is None:
            raise PatientNotFoundError(str(patient_id))

    async def _require_patient_encounter(self, encounter_id: UUID, patient_id: UUID) -> None:
        encounter = await self.session.scalar(
            select(Encounter.id).where(
                Encounter.id == encounter_id,
                Encounter.patient_id == patient_id,
            )
        )
        if encounter is None:
            raise ValueError("Document encounter must belong to the document patient")
