from uuid import uuid4

import pytest

from app.models.db import Attachment, ClinicalDocument, ImagingStudy, Patient
from app.seed.diagnostic_reports import seed_diagnostic_reports
from app.seed.documents import seed_clinical_documents
from app.seed.encounters import seed_encounters
from app.seed.imaging_studies import seed_imaging_studies


class EmptySeedResult:
    def scalar_one_or_none(self) -> None:
        return None


class SeedSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    async def execute(self, *_: object) -> EmptySeedResult:
        return EmptySeedResult()

    def add_all(self, records: list[object]) -> None:
        self.added.extend(records)

    def add(self, record: object) -> None:
        self.added.append(record)

    async def flush(self) -> None:
        return

    async def commit(self) -> None:
        return

    async def refresh(self, _: object) -> None:
        return


def synthetic_patients() -> list[Patient]:
    return [Patient(id=uuid4()) for _ in range(3)]


@pytest.mark.asyncio
async def test_three_patient_laboratory_seed_uses_native_report_ownership() -> None:
    session = SeedSession()
    patients = synthetic_patients()

    reports = await seed_diagnostic_reports(session, patients)

    assert len(reports) == 3
    assert {report.patient_id for report in reports} == {patient.id for patient in patients}
    for report in reports:
        assert report.observations
        assert all(
            observation.patient_id == report.patient_id for observation in report.observations
        )
        assert all(observation.diagnostic_report is report for observation in report.observations)


@pytest.mark.asyncio
async def test_encounter_seed_uses_patient_owned_encounters() -> None:
    session = SeedSession()
    patients = synthetic_patients()

    encounters = await seed_encounters(session, patients)

    assert len(encounters) == 3
    assert {encounter.patient_id for encounter in encounters} == {
        patient.id for patient in patients
    }


@pytest.mark.asyncio
async def test_synthetic_records_include_result_then_follow_up_encounter() -> None:
    session = SeedSession()
    patients = synthetic_patients()

    reports = await seed_diagnostic_reports(session, patients)
    encounters = await seed_encounters(session, patients)
    encounters_by_patient = {encounter.patient_id: encounter for encounter in encounters}

    assert all(
        report.effective_at is not None
        and encounters_by_patient[report.patient_id].started_at > report.effective_at
        for report in reports
    )


@pytest.mark.asyncio
async def test_imaging_study_seed_uses_patient_owned_native_study() -> None:
    session = SeedSession()
    patients = synthetic_patients()

    studies = await seed_imaging_studies(session, patients)

    assert len(studies) == 1
    assert isinstance(studies[0], ImagingStudy)
    assert studies[0].patient_id == patients[0].id
    assert studies[0].modality == "xray"


class SeedStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def upload(
        self, key: str, data: bytes, content_type: str, metadata: dict[str, str]
    ) -> str:
        assert content_type == "text/plain"
        assert metadata == {"seed": "synthetic"}
        self.objects[key] = data
        return key


@pytest.mark.asyncio
async def test_clinical_document_seed_uses_attachment_owned_storage() -> None:
    session = SeedSession()
    storage = SeedStorage()
    patients = synthetic_patients()

    documents = await seed_clinical_documents(session, storage, patients)

    attachments = [record for record in session.added if isinstance(record, Attachment)]
    assert len(documents) == 3
    assert {document.patient_id for document in documents} == {
        patient.id for patient in patients[:2]
    }
    assert len(attachments) == 3
    assert len(storage.objects) == 3
    assert all(isinstance(document, ClinicalDocument) for document in documents)
    assert {attachment.storage_key for attachment in attachments} == set(storage.objects)
