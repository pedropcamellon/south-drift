from __future__ import annotations

from flow_cases import FlowCase
from patient_payloads import PatientPayload
from playwright.sync_api import Locator, Page

from .session import log_step


def open_add_patient_dialog(page: Page) -> None:
    page.get_by_role("button", name="Add Patient").click(timeout=15000)
    page.get_by_role("heading", name="Add New Patient").wait_for(
        state="visible", timeout=15000
    )


def fill_patient_form(page: Page, patient: PatientPayload) -> None:
    page.get_by_placeholder("MRN").fill(patient.medical_record_number)
    page.get_by_placeholder("First Name").fill(patient.first_name)
    page.get_by_placeholder("Last Name").fill(patient.last_name)
    page.locator('input[name="dateOfBirth"]').fill(patient.date_of_birth)
    page.locator('select[name="gender"]').select_option(patient.gender)
    page.get_by_placeholder("Contact Info").fill(patient.contact_info)


def patient_row(page: Page, patient: PatientPayload) -> Locator:
    return page.get_by_role("row").filter(
        has=page.get_by_text(patient.medical_record_number, exact=True)
    )


def create_patient(page: Page, flow: FlowCase, patient: PatientPayload) -> None:
    log_step(flow.name, f"Creating patient {patient.full_name}")
    open_add_patient_dialog(page)
    fill_patient_form(page, patient)
    page.get_by_role("button", name="Add Patient").last.click(timeout=15000)
    patient_row(page, patient).wait_for(state="visible", timeout=20000)


def update_patient(
    page: Page,
    flow: FlowCase,
    original_patient: PatientPayload,
    updated_patient: PatientPayload,
) -> None:
    log_step(flow.name, f"Updating patient {original_patient.full_name}")
    row = patient_row(page, original_patient)
    row.get_by_role("button", name="Edit").click(timeout=15000)
    page.get_by_role("heading", name="Edit Patient").wait_for(
        state="visible", timeout=15000
    )
    fill_patient_form(page, updated_patient)
    page.get_by_role("button", name="Update Patient").click(timeout=15000)
    updated_row = patient_row(page, updated_patient)
    updated_row.wait_for(state="visible", timeout=20000)
    updated_row.get_by_text(updated_patient.contact_info, exact=True).wait_for(
        state="visible", timeout=15000
    )


def delete_patient(page: Page, flow: FlowCase, patient: PatientPayload) -> None:
    log_step(flow.name, f"Deleting patient {patient.full_name}")
    row = patient_row(page, patient)
    page.once("dialog", lambda dialog: dialog.accept())
    row.get_by_role("button", name="Delete").click(timeout=15000)
    row.wait_for(state="detached", timeout=20000)


def open_patient_history(page: Page, flow: FlowCase, patient: PatientPayload) -> None:
    log_step(flow.name, f"Opening history for {patient.full_name}")
    patient_row(page, patient).get_by_role("button", name="View History").click(
        timeout=15000
    )
    page.wait_for_url("**/patients/*", timeout=20000)
    page.get_by_role("button", name="New Encounter").wait_for(
        state="visible", timeout=15000
    )
