"""Diagnostic report endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions import Permission
from app.core.rbac import require_permission
from app.dependencies import get_diagnostic_report_service
from app.models.clinical import DiagnosticReportBundleCreate, DiagnosticReportResponse
from app.models.user import User
from app.services.diagnostic_report_service import DiagnosticReportService

router = APIRouter(prefix="/diagnostic-reports")


@router.get("/", response_model=list[DiagnosticReportResponse])
async def list_diagnostic_reports(
    patient_id: UUID = Query(..., alias="patientId"),
    _: User = Depends(require_permission(Permission.DOCUMENTS_READ)),
    service: DiagnosticReportService = Depends(get_diagnostic_report_service),
) -> list[DiagnosticReportResponse]:
    return await service.list_by_patient_id(patient_id)


@router.post("/", response_model=DiagnosticReportResponse, status_code=status.HTTP_201_CREATED)
async def create_diagnostic_report(
    bundle: DiagnosticReportBundleCreate,
    _: User = Depends(require_permission(Permission.DOCUMENTS_CREATE)),
    service: DiagnosticReportService = Depends(get_diagnostic_report_service),
) -> DiagnosticReportResponse:
    return await service.create(bundle)


@router.get("/{report_id}", response_model=DiagnosticReportResponse)
async def get_diagnostic_report(
    report_id: UUID,
    _: User = Depends(require_permission(Permission.DOCUMENTS_READ)),
    service: DiagnosticReportService = Depends(get_diagnostic_report_service),
) -> DiagnosticReportResponse:
    report = await service.get_by_id(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic report not found"
        )
    return report
