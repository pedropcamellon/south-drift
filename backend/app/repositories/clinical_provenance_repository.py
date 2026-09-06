"""Persistence helper for immutable provenance rows on native clinical records."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical import ProvenanceInput, ResourceType
from app.models.db import ClinicalProvenance


class ClinicalProvenanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        resource_type: ResourceType,
        resource_id: UUID,
        provenance: ProvenanceInput | None,
    ) -> None:
        if provenance is None:
            return

        self.session.add(
            ClinicalProvenance(
                resource_type=resource_type.value,
                resource_id=resource_id,
                **provenance.model_dump(),
            )
        )
        await self.session.flush()
