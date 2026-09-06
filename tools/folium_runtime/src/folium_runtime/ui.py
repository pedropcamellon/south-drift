"""Rich terminal presentation for the Folium runtime command."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()

# Leaf mark followed by a lowercase "folium" glyph, both drawn as plain ASCII blocks.
_LEAF = (
    "   ▄▄ ▄  ",
    "  ██ ███ ",
    " ██ ██ █ ",
    " █ █ ██  ",
    " ███     ",
    # " ██      ",
)
_F = ("  ▄▄▄ ", "  █   ", " ████ ", "  █   ", "  █   ")
_O = (" ▄▄▄  ", "█   █ ", "█   █ ", "█   █ ", " ███  ")
_L = ("▄    ", "█    ", "█    ", "█    ", "█████")
_I = ("▄", " ", "█", "█", "█")
_U = ("▄   ▄ ", "█   █ ", "█   █ ", "█   █ ", " ███  ")
_M = ("▄    ▄ ", "██  ██ ", "█ ██ █ ", "█    █ ", "█    █ ")

FOLIUM_WORDMARK = tuple(
    " ".join(glyph[row] for glyph in (_LEAF, _F, _O, _L, _I, _U, _M))
    for row in range(len(_LEAF))
)
WORDMARK_STYLES = ("bright_white", "white", "grey70", "grey58", "grey46")


def banner() -> None:
    console.print()
    for line, style in zip(FOLIUM_WORDMARK, WORDMARK_STYLES, strict=True):
        console.print(Text(line, style=f"bold {style}", justify="center"))
    console.print(
        Text(" ", justify="center"),
    )
    console.print(
        Text("[ LOCAL RUNTIME ]", style="bold black on white", justify="center")
    )
    console.print()


def error(message: str) -> None:
    console.print(f"[bold white on black] ERROR [/] {message}", style="white")


def notice(message: str) -> None:
    console.print(f"[bold black on white] INFO [/] {message}", style="white")


def endpoints(values: tuple[tuple[str, str], ...]) -> None:
    table = Table(
        title="LOCAL ENDPOINTS",
        box=box.SIMPLE_HEAVY,
        header_style="bold black on white",
    )
    table.add_column("Service", style="bold white")
    table.add_column("URL", style="white")
    for name, url in values:
        table.add_row(name, url)
    console.print(table)


def services(value: str) -> None:
    table = Table(
        title="COMPOSE SERVICES",
        box=box.SIMPLE_HEAVY,
        header_style="bold black on white",
    )
    table.add_column("Service", style="bold white")
    table.add_column("State", style="white")
    rows = [line.split("\t", maxsplit=1) for line in value.splitlines() if line.strip()]
    for row in rows:
        table.add_row(*row if len(row) == 2 else (row[0], "unknown"))
    if not rows:
        table.add_row("No Folium Compose services", "not running")
    console.print(table)
