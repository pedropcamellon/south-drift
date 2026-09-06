"""Seed native imaging studies for the synthetic patient cohort."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import ImagingStudy, Patient


async def seed_imaging_studies(
    session: AsyncSession, patients: list[Patient]
) -> list[ImagingStudy]:
    if len(patients) != 3:
        raise ValueError("Imaging study seeds require exactly three patients")

    existing = await session.execute(select(ImagingStudy.id).limit(1))
    if existing.scalar_one_or_none() is not None:
        return []

    studies = [
        ImagingStudy(
            patient_id=patients[0].id,
            modality="xray",
            performed_at=datetime(2026, 2, 20, 11, 0, tzinfo=UTC),
            external_study_id="synthetic-xray-001",
        )
    ]
    session.add_all(studies)
    await session.commit()
    for study in studies:
        await session.refresh(study)
    return studies
