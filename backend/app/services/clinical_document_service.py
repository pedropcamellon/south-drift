"""Business operations for clinical documents and stored attachments."""

from uuid import UUID

from app.core.exceptions import ClinicalDocumentNotFoundError
from app.models.clinical import ClinicalDocumentBundleCreate, ClinicalDocumentResponse
from app.models.db import Attachment
from app.repositories.clinical_document_repository import ClinicalDocumentRepository


class ClinicalDocumentService:
    def __init__(self, repository: ClinicalDocumentRepository):
        self.repository = repository

    async def list_by_patient_id(self, patient_id: UUID) -> list[ClinicalDocumentResponse]:
        documents = await self.repository.list_by_patient_id(patient_id)
        return [ClinicalDocumentResponse.model_validate(document) for document in documents]

    async def get_by_id(self, document_id: UUID) -> ClinicalDocumentResponse:
        document = await self.repository.get_by_id(document_id)
        if document is None:
            raise ClinicalDocumentNotFoundError(str(document_id))
        return ClinicalDocumentResponse.model_validate(document)

    async def create(self, bundle: ClinicalDocumentBundleCreate) -> ClinicalDocumentResponse:
        document = await self.repository.create(bundle)
        await self.repository.session.commit()
        return ClinicalDocumentResponse.model_validate(document)

    async def get_attachment(self, document_id: UUID, attachment_id: UUID) -> Attachment:
        attachment = await self.repository.get_attachment(document_id, attachment_id)
        if attachment is None:
            raise ClinicalDocumentNotFoundError(str(document_id))
        return attachment

    async def delete(self, document_id: UUID) -> None:
        if not await self.repository.delete(document_id):
            raise ClinicalDocumentNotFoundError(str(document_id))
        await self.repository.session.commit()
