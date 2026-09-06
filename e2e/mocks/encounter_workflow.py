from __future__ import annotations

import json

from playwright.sync_api import Page, Route

RoutePatterns = tuple[str, ...]


def request_json_object(route: Route) -> dict[str, object]:
    payload = route.request.post_data_json
    return payload if isinstance(payload, dict) else {}


def install_encounter_mocks(
    page: Page, encounter_id: str, transcript: str, mock_summary: bool = True
) -> RoutePatterns:
    encounter_url = f"**/api/v1/encounters/{encounter_id}"
    audio_url = f"**/api/v1/encounters/{encounter_id}/audio"
    note_url = f"**/api/v1/encounters/{encounter_id}/note"
    voice_note_status_url = f"**/api/v1/encounters/{encounter_id}/voice-note-status"
    route_patterns: list[str] = [
        encounter_url,
        audio_url,
        note_url,
        voice_note_status_url,
    ]
    state = {"transcribed_note": "", "saved_note": ""}

    def handle_encounter(route: Route) -> None:
        response = route.fetch()
        data = response.json()
        note_value = state["saved_note"] or state["transcribed_note"]
        if note_value:
            data["note"] = note_value
        route.fulfill(response=response, json=data)

    def handle_audio(route: Route) -> None:
        state["transcribed_note"] = transcript
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"message": "Audio accepted"}),
        )

    def handle_note(route: Route) -> None:
        payload = request_json_object(route)
        content = payload.get("content")
        state["saved_note"] = content if isinstance(content, str) else ""
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"content": state["saved_note"]}),
        )

    def handle_voice_note_status(route: Route) -> None:
        response = route.fetch()
        data = response.json()
        note_value = state["saved_note"] or state["transcribed_note"]
        data["status"] = "completed"
        data["encounter"]["note"] = note_value
        route.fulfill(response=response, json=data)

    def handle_summary(route: Route) -> None:
        payload = request_json_object(route)
        transcript_value = payload.get("transcript")
        note = transcript_value if isinstance(transcript_value, str) else ""
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

    page.route(encounter_url, handle_encounter)
    page.route(audio_url, handle_audio)
    page.route(note_url, handle_note)
    page.route(voice_note_status_url, handle_voice_note_status)
    if mock_summary:
        summarize_url = "**/api/v1/summarization/test"
        page.route(summarize_url, handle_summary)
        route_patterns.append(summarize_url)
    return tuple(route_patterns)


def remove_encounter_mocks(page: Page, routes: RoutePatterns) -> None:
    for route_url in routes:
        page.unroute(route_url)
