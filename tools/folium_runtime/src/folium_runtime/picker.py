"""Interactive service selection, isolated from Compose runtime orchestration."""

from __future__ import annotations

from dataclasses import dataclass

import questionary
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from questionary.constants import DEFAULT_SELECTED_POINTER
from questionary.prompts import common
from questionary.prompts.common import Choice, InquirerControl

SERVICES = (
    ("folium-postgres", "PostgreSQL"),
    ("folium-minio", "MinIO"),
    ("folium-temporal-postgres", "Temporal PostgreSQL"),
    ("folium-temporal", "Temporal server"),
    ("folium-temporal-ui", "Temporal UI"),
    ("folium-backend", "Backend API"),
    ("frontend", "Frontend"),
    ("folium-transcribe", "Transcription"),
    ("folium-summarize", "Local inference"),
    ("folium-chartreview-worker", "Chart review worker"),
    ("folium-voicenotes-worker", "Voice notes worker"),
    ("folium-prometheus", "Prometheus"),
    ("folium-grafana", "Grafana"),
    ("folium-loki", "Loki"),
    ("folium-promtail", "Promtail"),
)
BUILDABLE_SERVICES = frozenset(
    {
        "folium-backend",
        "frontend",
        "folium-transcribe",
        "folium-summarize",
        "folium-chartreview-worker",
        "folium-voicenotes-worker",
    }
)
OPTIONAL_SERVICES = frozenset({"folium-promtail"})

PICKER_STYLE = questionary.Style(
    [
        ("qmark", "fg:white bold"),
        ("question", "fg:white bold"),
        ("pointer", "fg:white bold"),
        ("highlighted", "fg:white bold"),
        ("selected", "fg:white bold"),
        ("checkbox-selected", "fg:white bold"),
        ("checkbox", "fg:white"),
    ]
)


@dataclass(frozen=True)
class ServiceSelection:
    services: list[str]
    build: list[str]
    recreate: list[str]


def select_services(
    service_states: dict[str, str] | None = None,
) -> ServiceSelection | None:
    """Return selected Compose services and services marked for b/x actions."""
    service_states = service_states or {}
    choices = [
        Choice(
            title=f"{label} ({service_states[name]})"
            if name in service_states
            else label,
            value=name,
            checked=name not in OPTIONAL_SERVICES,
        )
        for name, label in SERVICES
    ]
    titles = {choice.value: choice.title for choice in choices}
    build: set[str] = set()
    recreate: set[str] = set()
    control = InquirerControl(choices, None, pointer=DEFAULT_SELECTED_POINTER)

    def sync_title(choice: Choice) -> None:
        marks = []
        if choice.value in build:
            marks.append("build")
        if choice.value in recreate:
            marks.append("recreate")
        choice.title = (
            f"{titles[choice.value]} [{' | '.join(marks)}]"
            if marks
            else titles[choice.value]
        )

    def prompt_tokens():
        tokens = [
            ("class:question", "Select services to run"),
        ]
        tokens.append(
            (
                "class:instruction",
                "\n  Space toggle  b build image  x recreate  a all  i invert  Enter run  Ctrl-C cancel",
            )
        )
        return tokens

    layout = common.create_inquirer_layout(control, prompt_tokens)
    bindings = KeyBindings()

    @bindings.add(Keys.ControlC, eager=True)
    @bindings.add(Keys.ControlQ, eager=True)
    def cancel(event):
        event.app.exit(exception=KeyboardInterrupt)

    @bindings.add(" ", eager=True)
    def toggle(_event):
        pointed = control.get_pointed_at().value
        if pointed in control.selected_options:
            control.selected_options.remove(pointed)
        else:
            control.selected_options.append(pointed)

    def toggle_mark(marked: set[str]) -> None:
        choice = control.get_pointed_at()
        if marked is build and choice.value not in BUILDABLE_SERVICES:
            return
        if choice.value in marked:
            marked.remove(choice.value)
        else:
            marked.add(choice.value)
            if choice.value not in control.selected_options:
                control.selected_options.append(choice.value)
        sync_title(choice)

    @bindings.add("b", eager=True)
    def toggle_build(_event):
        toggle_mark(build)

    @bindings.add("x", eager=True)
    def toggle_recreate(_event):
        toggle_mark(recreate)

    @bindings.add("a", eager=True)
    def toggle_all(_event):
        control.selected_options = (
            []
            if len(control.selected_options) == len(choices)
            else [choice.value for choice in choices]
        )

    @bindings.add("i", eager=True)
    def invert(_event):
        control.selected_options = [
            choice.value
            for choice in choices
            if choice.value not in control.selected_options
        ]

    @bindings.add(Keys.Down, eager=True)
    @bindings.add("j", eager=True)
    def down(_event):
        control.select_next()

    @bindings.add(Keys.Up, eager=True)
    @bindings.add("k", eager=True)
    def up(_event):
        control.select_previous()

    @bindings.add(Keys.ControlM, eager=True)
    def submit(event):
        event.app.exit(
            result=[choice.value for choice in control.get_selected_values()]
        )

    @bindings.add(Keys.Any)
    def consume(_event):
        return

    try:
        selected = Application(
            layout=layout, key_bindings=bindings, style=PICKER_STYLE
        ).run()
    except KeyboardInterrupt:
        return None
    selected_set = set(selected)
    return ServiceSelection(
        selected, sorted(build & selected_set), sorted(recreate & selected_set)
    )
