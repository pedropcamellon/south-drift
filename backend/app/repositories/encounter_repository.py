"""Persistence operations for patient-owned encounters and narratives."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import PatientNotFoundError
from app.models.clinical import (
    EncounterCreate,
    EncounterNarrativeCreate,
    EncounterNarrativeUpdate,
    EncounterUpdate,
    ResourceType,
)
from app.models.db import Encounter, EncounterNarrative, Patient
from app.repositories.clinical_provenance_repository import ClinicalProvenanceRepository


class EncounterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_patient_id(self, patient_id: UUID) -> list[Encounter]:
        result = await self.session.execute(
            select(Encounter)
            .where(Encounter.patient_id == patient_id)
            .order_by(Encounter.started_at.desc())
            .options(selectinload(Encounter.narratives))
        )
        return list(result.scalars())

    async def get_by_id(self, encounter_id: UUID) -> Encounter | None:
        result = await self.session.execute(
            select(Encounter)
            .where(Encounter.id == encounter_id)
            .options(selectinload(Encounter.narratives))
        )
        return result.scalar_one_or_none()

    async def create(self, encounter_input: EncounterCreate) -> Encounter:
        await self._require_patient(encounter_input.patient_id)
        if encounter_input.prior_encounter_id is not None:
            await self._require_prior_encounter(
                encounter_input.prior_encounter_id, encounter_input.patient_id
            )

        encounter_data = encounter_input.model_dump(exclude={"provenance"})
        encounter_data["encounter_type"] = encounter_input.encounter_type.value
        encounter_data["purpose"] = encounter_input.purpose.value
        encounter_data["status"] = encounter_input.status.value
        encounter = Encounter(**encounter_data)
        self.session.add(encounter)
        await self.session.flush()
        await ClinicalProvenanceRepository(self.session).create(
            ResourceType.ENCOUNTER, encounter.id, encounter_input.provenance
        )
        return encounter

    async def create_narrative(
        self, encounter_id: UUID, narrative_input: EncounterNarrativeCreate
    ) -> EncounterNarrative | None:
        encounter = await self.get_by_id(encounter_id)
        if encounter is None:
            return None

        narrative_data = narrative_input.model_dump(exclude={"encounter_id", "provenance"})
        narrative_data["status"] = narrative_input.status.value
        narrative = EncounterNarrative(
            patient_id=encounter.patient_id,
            encounter_id=encounter.id,
            **narrative_data,
        )
        self.session.add(narrative)
        await self.session.flush()
        await ClinicalProvenanceRepository(self.session).create(
            ResourceType.ENCOUNTER_NARRATIVE, narrative.id, narrative_input.provenance
        )
        return narrative

    async def update(
        self, encounter_id: UUID, encounter_input: EncounterUpdate
    ) -> Encounter | None:
        encounter = await self.get_by_id(encounter_id)
        if encounter is None:
            return None

        for field, value in encounter_input.model_dump(exclude_unset=True).items():
            if field in {"encounter_type", "purpose", "status"} and value is not None:
                value = value.value
            setattr(encounter, field, value)
        await self.session.flush()
        return encounter

    async def replace_narrative(
        self, encounter_id: UUID, narrative_input: EncounterNarrativeUpdate
    ) -> Encounter | None:
        encounter = await self.get_by_id(encounter_id)
        if encounter is None:
            return None

        narrative = encounter.narratives[-1] if encounter.narratives else None
        if narrative is None:
            narrative = EncounterNarrative(
                patient_id=encounter.patient_id,
                encounter_id=encounter.id,
                content=narrative_input.content,
                status=narrative_input.status.value,
            )
            self.session.add(narrative)
        else:
            narrative.content = narrative_input.content
            narrative.status = narrative_input.status.value
        await self.session.flush()
        return await self.get_by_id(encounter_id)

    async def delete(self, encounter_id: UUID) -> bool:
        encounter = await self.get_by_id(encounter_id)
        if encounter is None:
            return False
        await self.session.delete(encounter)
        await self.session.flush()
        return True

    async def _require_patient(self, patient_id: UUID) -> None:
        patient = await self.session.scalar(select(Patient.id).where(Patient.id == patient_id))
        if patient is None:
            raise PatientNotFoundError(str(patient_id))

    async def _require_prior_encounter(self, encounter_id: UUID, patient_id: UUID) -> None:
        prior_encounter = await self.session.scalar(
            select(Encounter.id).where(
                Encounter.id == encounter_id,
                Encounter.patient_id == patient_id,
            )
        )
        if prior_encounter is None:
            raise ValueError("Prior encounter must belong to the encounter patient")
