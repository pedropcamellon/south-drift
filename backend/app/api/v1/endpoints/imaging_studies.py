"""Imaging study endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.dependencies import get_imaging_study_service
from app.models.clinical import ImagingStudyCreate, ImagingStudyResponse
from app.models.user import User
from app.services.imaging_study_service import ImagingStudyService

router = APIRouter(prefix="/imaging-studies")


@router.get("/", response_model=list[ImagingStudyResponse])
async def list_imaging_studies(
    patient_id: UUID = Query(..., alias="patientId"),
    _: User = Depends(require_permission(Permission.DOCUMENTS_READ)),
    service: ImagingStudyService = Depends(get_imaging_study_service),
) -> list[ImagingStudyResponse]:
    return await service.list_by_patient_id(patient_id)


@router.post("/", response_model=ImagingStudyResponse, status_code=status.HTTP_201_CREATED)
async def create_imaging_study(
    study: ImagingStudyCreate,
    _: User = Depends(require_permission(Permission.DOCUMENTS_CREATE)),
    service: ImagingStudyService = Depends(get_imaging_study_service),
) -> ImagingStudyResponse:
    try:
        return await service.create(study)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.get("/{study_id}", response_model=ImagingStudyResponse)
async def get_imaging_study(
    study_id: UUID,
    _: User = Depends(require_permission(Permission.DOCUMENTS_READ)),
    service: ImagingStudyService = Depends(get_imaging_study_service),
) -> ImagingStudyResponse:
    study = await service.get_by_id(study_id)
    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imaging study not found")
    return study
