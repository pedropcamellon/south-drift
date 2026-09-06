from __future__ import annotations

from flow_cases import FlowCase
from playwright.sync_api import Page

from .session import log_step


def create_encounter(page: Page, flow: FlowCase, title: str) -> str:
    log_step(flow.name, f"Creating encounter {title}")
    page.get_by_role("button", name="New Encounter").click(timeout=15000)
    page.get_by_role("heading", name="Add Encounter").wait_for(
        state="visible", timeout=15000
    )

    page.locator("#encounterType").click(timeout=15000)
    page.get_by_role("option", name="Outpatient").click(timeout=15000)
    page.get_by_label("Title").fill(title)
    page.get_by_label("Description").fill(
        "Provider voice note workflow created by Playwright."
    )
    page.get_by_label("Clinician name").fill("Dr. Folium")

    with page.expect_response(
        lambda response: (
            response.request.method == "POST"
            and "/api/v1/encounters" in response.url
            and response.status == 201
        ),
        timeout=20000,
    ) as response_info:
        page.get_by_role("button", name="Create Encounter").click(timeout=15000)

    encounter = response_info.value.json()
    page.get_by_role("button", name=f"View details for {title}").wait_for(
        state="visible", timeout=20000
    )
    return encounter["id"]


def open_encounter_details(page: Page, flow: FlowCase, title: str) -> None:
    log_step(flow.name, f"Opening encounter details for {title}")
    page.get_by_role("button", name=f"View details for {title}").click(timeout=15000)
    page.get_by_role("heading", name="Encounter Details").wait_for(
        state="visible", timeout=15000
    )


def record_and_submit_audio(page: Page, flow: FlowCase, transcript: str) -> None:
    log_step(flow.name, "Recording and submitting audio")
    page.get_by_role("button", name="Record").click(timeout=15000)
    page.get_by_role("button", name="Stop Recording").wait_for(
        state="visible", timeout=15000
    )
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Stop Recording").click(timeout=15000)
    page.get_by_role("button", name="Submit Audio").wait_for(
        state="visible", timeout=15000
    )
    page.get_by_role("button", name="Submit Audio").click(timeout=15000)

    page.get_by_text("Transcription complete!", exact=True).wait_for(
        state="visible", timeout=15000
    )
    page.get_by_text(transcript, exact=True).wait_for(state="visible", timeout=15000)


def edit_and_save_note(page: Page, flow: FlowCase, note: str) -> None:
    log_step(flow.name, "Editing and saving transcribed note")
    page.get_by_role("button", name="Edit Note").click(timeout=15000)
    note_editor = page.locator("textarea").first
    note_editor.fill(note)
    page.get_by_role("button", name="Save").click(timeout=15000)
    page.get_by_text(note, exact=True).wait_for(state="visible", timeout=15000)


def generate_and_assert_summary(
    page: Page, flow: FlowCase, timeout_ms: int = 15000
) -> None:
    log_step(flow.name, "Generating summary from saved note")
    page.get_by_role("button", name="Generate Summary").click(timeout=15000)
    page.get_by_role("button", name="Edit Summary").wait_for(
        state="visible", timeout=timeout_ms
    )
    page.get_by_text(
        "No summary available. Generate one from your notes.", exact=True
    ).wait_for(state="hidden", timeout=timeout_ms)


def close_encounter_details(page: Page) -> None:
    dialog = page.get_by_role("dialog")
    dialog.get_by_role("button", name="Close").first.click(timeout=15000)
