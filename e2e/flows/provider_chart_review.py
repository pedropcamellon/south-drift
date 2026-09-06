from __future__ import annotations

import re

from flow_cases import FlowCase
from playwright.sync_api import Page, expect
from settings import CHART_REVIEW_WAIT_MS
from ui import close_encounter_details, open_encounter_details
from ui.session import log_step

SEEDED_PATIENT_MRN = "MRN-2026-001"
FOLLOW_UP_TITLE = "Synthetic follow-up encounter"


def run_provider_chart_review_flow(page: Page, base_url: str, flow: FlowCase) -> None:
    """Run the real local chart-review workflow against a synthetic seeded encounter."""
    log_step(flow.name, "Opening seeded follow-up encounter for chart review")
    page.goto(f"{base_url}/provider", wait_until="domcontentloaded")
    seeded_patient = page.get_by_role("row").filter(
        has=page.get_by_text(SEEDED_PATIENT_MRN, exact=True)
    )
    seeded_patient.get_by_role("button", name="View History").click(timeout=15000)
    page.wait_for_url("**/patients/*", timeout=20000)
    open_encounter_details(page, flow, FOLLOW_UP_TITLE)

    dialog = page.get_by_role("dialog")
    draft_button = dialog.get_by_role(
        "button", name=re.compile(r"Generate (new )?draft")
    )
    processing_message = dialog.get_by_text("Draft review is processing.", exact=True)
    if processing_message.is_visible():
        processing_message.wait_for(state="hidden", timeout=CHART_REVIEW_WAIT_MS)
    expect(draft_button).to_be_enabled(timeout=15000)
    draft_button.click(timeout=15000)
    processing_message.wait_for(state="visible", timeout=15000)
    expect(dialog.get_by_role("heading", name="Review rationale")).to_have_count(0)
    expect(dialog.get_by_role("heading", name="Source references")).to_have_count(0)
    expect(dialog.get_by_text("Confidence:", exact=False)).to_have_count(0)
    processing_message.wait_for(state="hidden", timeout=CHART_REVIEW_WAIT_MS)

    dialog.get_by_text(re.compile(r"^Confidence: (low|medium|high)$")).wait_for(
        state="visible", timeout=15000
    )
    expect(dialog.get_by_text("NaN%", exact=False)).to_have_count(0)
    expect(
        dialog.locator(
            "section[aria-labelledby='chart-review-heading'] > div:last-child > p"
        )
    ).not_to_be_empty(timeout=15000)
    dialog.get_by_role("heading", name="Source references").wait_for(
        state="visible", timeout=15000
    )
    dialog.get_by_text(
        "Synthetic follow-up encounter - description", exact=False
    ).wait_for(state="visible", timeout=15000)
    expect(dialog.get_by_text("encounter-description:", exact=False)).to_have_count(0)
    dialog.get_by_role("heading", name="Review rationale").wait_for(
        state="visible", timeout=15000
    )
    close_encounter_details(page)
