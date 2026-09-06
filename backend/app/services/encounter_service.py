"""Business operations for patient-owned encounters."""

from uuid import UUID

from app.core.exceptions import EncounterNotFoundError
from app.models.clinical import (
    EncounterCreate,
    EncounterNarrativeCreate,
    EncounterNarrativeResponse,
    EncounterNarrativeUpdate,
    EncounterResponse,
    EncounterUpdate,
)
from app.repositories.encounter_repository import EncounterRepository


class EncounterService:
    def __init__(self, repository: EncounterRepository):
        self.repository = repository

    async def list_by_patient_id(self, patient_id: UUID) -> list[EncounterResponse]:
        encounters = await self.repository.list_by_patient_id(patient_id)
        return [EncounterResponse.model_validate(encounter) for encounter in encounters]

    async def get_by_id(self, encounter_id: UUID) -> EncounterResponse:
        encounter = await self.repository.get_by_id(encounter_id)
        if encounter is None:
            raise EncounterNotFoundError(str(encounter_id))
        return EncounterResponse.model_validate(encounter)

    async def create(self, encounter_input: EncounterCreate) -> EncounterResponse:
        encounter = await self.repository.create(encounter_input)
        await self.repository.session.commit()
        await self.repository.session.refresh(encounter, attribute_names=["narratives"])
        return self._to_response(encounter)

    async def update(
        self, encounter_id: UUID, encounter_input: EncounterUpdate
    ) -> EncounterResponse:
        encounter = await self.repository.update(encounter_id, encounter_input)
        if encounter is None:
            raise EncounterNotFoundError(str(encounter_id))
        await self.repository.session.commit()
        return self._to_response(encounter)

    async def replace_narrative(
        self, encounter_id: UUID, narrative_input: EncounterNarrativeUpdate
    ) -> EncounterResponse:
        encounter = await self.repository.replace_narrative(encounter_id, narrative_input)
        if encounter is None:
            raise EncounterNotFoundError(str(encounter_id))
        await self.repository.session.commit()
        return self._to_response(encounter)

    async def delete(self, encounter_id: UUID) -> None:
        deleted = await self.repository.delete(encounter_id)
        if not deleted:
            raise EncounterNotFoundError(str(encounter_id))
        await self.repository.session.commit()

    async def create_narrative(
        self, encounter_id: UUID, narrative_input: EncounterNarrativeCreate
    ) -> EncounterNarrativeResponse:
        if narrative_input.encounter_id != encounter_id:
            raise ValueError("Narrative encounter ID must match the URL encounter ID")
        narrative = await self.repository.create_narrative(encounter_id, narrative_input)
        if narrative is None:
            raise EncounterNotFoundError(str(encounter_id))
        await self.repository.session.commit()
        return EncounterNarrativeResponse.model_validate(narrative)

    @staticmethod
    def _to_response(encounter) -> EncounterResponse:
        note = encounter.narratives[-1].content if encounter.narratives else None
        return EncounterResponse.model_validate(encounter).model_copy(update={"note": note})
