"""Seed native clinical documents with stored synthetic attachments."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Attachment, ClinicalDocument, Patient
from app.services.storage.base import ObjectStorageProvider


async def seed_clinical_documents(
    session: AsyncSession,
    storage: ObjectStorageProvider,
    patients: list[Patient],
) -> list[ClinicalDocument]:
    """Seed native documents and attachments for the synthetic patient cohort."""
    if len(patients) != 3:
        raise ValueError("Clinical document seeds require exactly three patients")

    result = await session.execute(select(ClinicalDocument).limit(1))
    if result.scalar_one_or_none():
        return []

    document_seeds = [
        (
            patients[0],
            "external_record",
            "Chest X-Ray Results",
            datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            "chest-xray-summary.txt",
            b"Synthetic chest X-ray report: no acute cardiopulmonary finding.\n",
        ),
        (
            patients[0],
            "patient_submission",
            "Patient Intake Form",
            datetime(2026, 2, 28, 9, 0, tzinfo=UTC),
            "patient-intake.txt",
            b"Synthetic intake record for local development only.\n",
        ),
        (
            patients[1],
            "external_record",
            "Laboratory Results Attachment",
            datetime(2026, 2, 28, 14, 30, tzinfo=UTC),
            "preventive-blood-panel.txt",
            b"Synthetic laboratory attachment. Structured values are in DiagnosticReport.\n",
        ),
    ]

    documents: list[ClinicalDocument] = []
    for patient, category, title, authored_at, file_name, data in document_seeds:
        storage_key = f"documents/synthetic/{patient.id}/{file_name}"
        await storage.upload(
            key=storage_key,
            data=data,
            content_type="text/plain",
            metadata={"seed": "synthetic"},
        )
        document = ClinicalDocument(
            patient_id=patient.id,
            category=category,
            status="final",
            title=title,
            authored_at=authored_at,
        )
        session.add(document)
        await session.flush()
        session.add(
            Attachment(
                clinical_document_id=document.id,
                storage_key=storage_key,
                file_name=file_name,
                mime_type="text/plain",
                byte_size=len(data),
            )
        )
        documents.append(document)

    await session.commit()

    for document in documents:
        await session.refresh(document)

    return documents
