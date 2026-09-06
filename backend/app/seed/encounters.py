"""Seed native encounters for the synthetic patient cohort."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Encounter, Patient


async def seed_encounters(session: AsyncSession, patients: list[Patient]) -> list[Encounter]:
    """Seed one patient-owned encounter per synthetic patient."""
    if len(patients) != 3:
        raise ValueError("Encounter seeds require exactly three patients")

    existing = await session.execute(select(Encounter.id).limit(1))
    if existing.scalar_one_or_none() is not None:
        return []

    encounters = [
        Encounter(
            patient_id=patient.id,
            encounter_type="outpatient",
            purpose="follow_up",
            status="completed",
            title="Synthetic follow-up encounter",
            started_at=datetime(2026, 3, index + 1, 10, 0, tzinfo=UTC),
            description="Synthetic encounter used only for local workflow review.",
        )
        for index, patient in enumerate(patients)
    ]
    session.add_all(encounters)
    await session.flush()
    return encounters
