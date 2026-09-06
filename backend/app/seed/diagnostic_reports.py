"""Seed native diagnostic reports for the synthetic patient cohort."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import DiagnosticReport, Observation, Patient


async def seed_diagnostic_reports(
    session: AsyncSession, patients: list[Patient]
) -> list[DiagnosticReport]:
    """Seed one structured laboratory report for each synthetic patient."""
    if len(patients) != 3:
        raise ValueError("Diagnostic report seeds require exactly three patients")

    existing = await session.execute(select(DiagnosticReport).limit(1))
    if existing.scalar_one_or_none():
        return []

    reports = [
        DiagnosticReport(
            patient_id=patients[0].id,
            status="final",
            title="Annual Wellness Laboratory Panel",
            effective_at=datetime(2026, 2, 15, 9, 0, tzinfo=UTC),
            issued_at=datetime(2026, 2, 15, 15, 0, tzinfo=UTC),
            conclusion="Fasting glucose and lipid values are within the expected range.",
            observations=[
                Observation(
                    patient_id=patients[0].id,
                    status="final",
                    code="glucose",
                    display="Fasting blood glucose",
                    value_type="quantity",
                    value="95",
                    unit="mg/dL",
                    effective_at=datetime(2026, 2, 15, 9, 0, tzinfo=UTC),
                ),
                Observation(
                    patient_id=patients[0].id,
                    status="final",
                    code="total-cholesterol",
                    display="Total cholesterol",
                    value_type="quantity",
                    value="185",
                    unit="mg/dL",
                    effective_at=datetime(2026, 2, 15, 9, 0, tzinfo=UTC),
                ),
            ],
        ),
        DiagnosticReport(
            patient_id=patients[1].id,
            status="final",
            title="Preventive Blood Panel",
            effective_at=datetime(2026, 2, 28, 8, 30, tzinfo=UTC),
            issued_at=datetime(2026, 2, 28, 14, 30, tzinfo=UTC),
            conclusion="Routine preventive laboratory values are within the expected range.",
            observations=[
                Observation(
                    patient_id=patients[1].id,
                    status="final",
                    code="hemoglobin",
                    display="Hemoglobin",
                    value_type="quantity",
                    value="14.8",
                    unit="g/dL",
                    effective_at=datetime(2026, 2, 28, 8, 30, tzinfo=UTC),
                ),
                Observation(
                    patient_id=patients[1].id,
                    status="final",
                    code="fasting-glucose",
                    display="Fasting blood glucose",
                    value_type="quantity",
                    value="89",
                    unit="mg/dL",
                    effective_at=datetime(2026, 2, 28, 8, 30, tzinfo=UTC),
                ),
            ],
        ),
        DiagnosticReport(
            patient_id=patients[2].id,
            status="final",
            title="Comprehensive Metabolic Panel",
            effective_at=datetime(2026, 3, 1, 8, 15, tzinfo=UTC),
            issued_at=datetime(2026, 3, 1, 14, 0, tzinfo=UTC),
            conclusion="Kidney function and electrolytes are within the expected range.",
            observations=[
                Observation(
                    patient_id=patients[2].id,
                    status="final",
                    code="creatinine",
                    display="Creatinine",
                    value_type="quantity",
                    value="0.9",
                    unit="mg/dL",
                    effective_at=datetime(2026, 3, 1, 8, 15, tzinfo=UTC),
                ),
                Observation(
                    patient_id=patients[2].id,
                    status="final",
                    code="potassium",
                    display="Potassium",
                    value_type="quantity",
                    value="4.2",
                    unit="mmol/L",
                    effective_at=datetime(2026, 3, 1, 8, 15, tzinfo=UTC),
                ),
            ],
        ),
    ]

    session.add_all(reports)
    await session.commit()

    for report in reports:
        await session.refresh(report)

    return reports
