from __future__ import annotations

import json

from playwright.sync_api import Page, Route

RoutePatterns = tuple[str, ...]


def install_summary_page_mocks(
    page: Page, transcript: str
) -> tuple[str, str, RoutePatterns]:
    patient_id = "00000000-0000-0000-0000-000000000101"
    encounter_id = "00000000-0000-0000-0000-000000000201"
    patient_url = f"**/api/v1/patients/{patient_id}"
    timeline_url = f"**/api/v1/patients/{patient_id}/timeline*"
    encounter_url = f"**/api/v1/encounters/{encounter_id}"
    documents_url = f"**/api/v1/clinical-documents/?patientId={patient_id}*"
    summarize_url = "**/api/v1/summarization"

    patient_payload = {
        "id": patient_id,
        "medicalRecordNumber": "E2E-SUMMARY-001",
        "firstName": "Taylor",
        "lastName": "Summary",
        "dateOfBirth": "1992-04-15",
        "gender": "Female",
        "contactInfo": "taylor.summary@folium.test",
        "medicalImages": [],
        "clinicalSummaries": [],
    }
    encounter_payload = {
        "id": encounter_id,
        "createdAt": "2026-03-26T10:00:00Z",
        "createdBy": "provider@folium.com",
        "description": "Mocked summary scenario encounter.",
        "startedAt": "2026-03-26T10:00:00Z",
        "isCompliant": True,
        "location": "Mock Clinic",
        "narratives": [],
        "note": transcript,
        "summary": "",
        "patientId": patient_id,
        "clinicianId": "provider-001",
        "clinicianName": "Dr. Folium",
        "title": "Mock Summary Encounter",
        "encounterType": "outpatient",
        "purpose": "follow_up",
        "status": "completed",
        "updatedAt": "2026-03-26T10:00:00Z",
        "updatedBy": "provider@folium.com",
    }
    timeline_payload = {
        "entries": [
            {
                "id": encounter_id,
                "kind": "encounter",
                "patientId": patient_id,
                "occurredAt": encounter_payload["startedAt"],
                "title": encounter_payload["title"],
                "status": encounter_payload["status"],
                "encounter": encounter_payload,
            }
        ],
        "nextCursor": None,
    }
    route_patterns = (
        patient_url,
        timeline_url,
        encounter_url,
        documents_url,
        summarize_url,
    )

    def handle_patient(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(patient_payload),
        )

    def handle_timeline(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(timeline_payload),
        )

    def handle_encounter(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(encounter_payload),
        )

    def handle_documents(route: Route) -> None:
        route.fulfill(status=200, content_type="application/json", body="[]")

    def handle_summary(route: Route) -> None:
        payload = route.request.post_data_json
        note = payload.get("transcript", "")
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "summary": "SOAP summary generated in e2e",
                    "structured_data": {
                        "chief_complaint": "Improved sleep and residual cough",
                        "subjective": note,
                        "objective": "Afebrile and speaking clearly during follow-up.",
                        "assessment": "Upper respiratory symptoms are improving.",
                        "plan": "Continue hydration, monitor cough, and follow up if symptoms worsen.",
                        "clinical_tags": ["follow-up", "respiratory"],
                        "icd_codes": ["J06.9"],
                        "action_items": [
                            "Continue supportive care",
                            "Return if fever recurs",
                        ],
                    },
                    "processing_time": 0.25,
                    "model_used": "playwright-e2e",
                    "provider": "mock",
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    },
                }
            ),
        )

    page.route(patient_url, handle_patient)
    page.route(timeline_url, handle_timeline)
    page.route(encounter_url, handle_encounter)
    page.route(documents_url, handle_documents)
    page.route(summarize_url, handle_summary)

    return patient_id, encounter_payload["title"], route_patterns


def remove_summary_page_mocks(page: Page, routes: RoutePatterns) -> None:
    for route_url in routes:
        page.unroute(route_url)
