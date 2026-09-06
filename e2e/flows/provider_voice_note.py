from __future__ import annotations

from flow_cases import FlowCase
from mocks import install_encounter_mocks, remove_encounter_mocks
from patient_payloads import build_provider_test_patient
from playwright.sync_api import Page
from ui import (
    create_encounter,
    create_patient,
    delete_patient,
    open_encounter_details,
    open_patient_history,
    patient_row,
    record_and_submit_audio,
)


def run_provider_voice_note_flow(
    page: Page, base_url: str, flow: FlowCase, transcript: str
) -> None:
    patient = build_provider_test_patient()
    encounter_title = f"Voice Note {patient.medical_record_number}"

    create_patient(page, flow, patient)
    try:
        open_patient_history(page, flow, patient)
        encounter_id = create_encounter(page, flow, encounter_title)
        routes = install_encounter_mocks(page, encounter_id, transcript)
        try:
            open_encounter_details(page, flow, encounter_title)
            record_and_submit_audio(page, flow, transcript)
        finally:
            remove_encounter_mocks(page, routes)
    finally:
        page.goto(f"{base_url}{flow.expected_path}", wait_until="domcontentloaded")
        patient_row(page, patient).wait_for(state="visible", timeout=20000)
        delete_patient(page, flow, patient)
