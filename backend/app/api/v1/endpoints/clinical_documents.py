"""Clinical document and attachment endpoints."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import RedirectResponse

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.dependencies import get_clinical_document_service, get_storage_provider
from app.models.clinical import (
    AttachmentCreate,
    ClinicalDocumentBundleCreate,
    ClinicalDocumentCategory,
    ClinicalDocumentCreate,
    ClinicalDocumentResponse,
    ClinicalRecordStatus,
)
from app.models.user import User
from app.services.clinical_document_service import ClinicalDocumentService
from app.services.storage.base import ObjectStorageProvider

router = APIRouter(prefix="/clinical-documents")

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".txt", ".docx", ".doc"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.get("/", response_model=list[ClinicalDocumentResponse])
async def list_clinical_documents(
    patient_id: UUID = Query(..., alias="patientId"),
    _: User = Depends(require_permission(Permission.DOCUMENTS_READ)),
    service: ClinicalDocumentService = Depends(get_clinical_document_service),
) -> list[ClinicalDocumentResponse]:
    return await service.list_by_patient_id(patient_id)


@router.get("/{document_id}", response_model=ClinicalDocumentResponse)
async def get_clinical_document(
    document_id: UUID,
    _: User = Depends(require_permission(Permission.DOCUMENTS_READ)),
    service: ClinicalDocumentService = Depends(get_clinical_document_service),
) -> ClinicalDocumentResponse:
    return await service.get_by_id(document_id)


@router.post("/", response_model=ClinicalDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_clinical_document(
    bundle: ClinicalDocumentBundleCreate,
    _: User = Depends(require_permission(Permission.DOCUMENTS_CREATE)),
    service: ClinicalDocumentService = Depends(get_clinical_document_service),
) -> ClinicalDocumentResponse:
    try:
        return await service.create(bundle)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post(
    "/upload", response_model=ClinicalDocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_clinical_document(
    file: UploadFile = File(...),
    patient_id: UUID = Form(..., alias="patientId"),
    category: ClinicalDocumentCategory = Form(...),
    title: str = Form(...),
    status_value: ClinicalRecordStatus = Form(ClinicalRecordStatus.FINAL, alias="status"),
    encounter_id: UUID | None = Form(None, alias="encounterId"),
    _: User = Depends(require_permission(Permission.DOCUMENTS_CREATE)),
    storage: ObjectStorageProvider = Depends(get_storage_provider),
    service: ClinicalDocumentService = Depends(get_clinical_document_service),
) -> ClinicalDocumentResponse:
    file_name = Path(file.filename or "document").name
    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")
    mime_type = file.content_type or "application/octet-stream"
    storage_key = (
        f"documents/{patient_id}/{datetime.now(UTC):%Y%m%d_%H%M%S}_{uuid4().hex}_{file_name}"
    )
    await storage.upload(key=storage_key, data=content, content_type=mime_type, metadata={})
    return await service.create(
        ClinicalDocumentBundleCreate(
            document=ClinicalDocumentCreate(
                patientId=patient_id,
                category=category,
                status=status_value,
                title=title,
                encounterId=encounter_id,
            ),
            attachments=[
                AttachmentCreate(
                    storageKey=storage_key,
                    fileName=file_name,
                    mimeType=mime_type,
                    byteSize=len(content),
                )
            ],
        )
    )


@router.get("/{document_id}/attachments/{attachment_id}/download")
async def download_attachment(
    document_id: UUID,
    attachment_id: UUID,
    _: User = Depends(require_permission(Permission.DOCUMENTS_READ)),
    service: ClinicalDocumentService = Depends(get_clinical_document_service),
    storage: ObjectStorageProvider = Depends(get_storage_provider),
) -> RedirectResponse:
    attachment = await service.get_attachment(document_id, attachment_id)
    url = await storage.get_presigned_url(attachment.storage_key, expiration=3600)
    return RedirectResponse(url=url)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clinical_document(
    document_id: UUID,
    _: User = Depends(require_permission(Permission.DOCUMENTS_DELETE)),
    service: ClinicalDocumentService = Depends(get_clinical_document_service),
) -> None:
    await service.delete(document_id)
