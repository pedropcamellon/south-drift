"""Business operations for patient-owned imaging studies."""

from uuid import UUID

from app.models.clinical import ImagingStudyCreate, ImagingStudyResponse
from app.repositories.imaging_study_repository import ImagingStudyRepository


class ImagingStudyService:
    def __init__(self, repository: ImagingStudyRepository):
        self.repository = repository

    async def list_by_patient_id(self, patient_id: UUID) -> list[ImagingStudyResponse]:
        studies = await self.repository.list_by_patient_id(patient_id)
        return [ImagingStudyResponse.model_validate(study) for study in studies]

    async def get_by_id(self, study_id: UUID) -> ImagingStudyResponse | None:
        study = await self.repository.get_by_id(study_id)
        return ImagingStudyResponse.model_validate(study) if study is not None else None

    async def create(self, study_input: ImagingStudyCreate) -> ImagingStudyResponse:
        study = await self.repository.create(study_input)
        await self.repository.session.commit()
        return ImagingStudyResponse.model_validate(study)
