"""Render a :class:`ChecklistResult` as a rich terminal report or JSON."""

from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table
from rich.text import Text

from .checklist import CategoryResult, ChecklistResult


def to_json(result: ChecklistResult, *, indent: int = 2) -> str:
    return json.dumps(result.to_dict(), indent=indent)


def _pct_color(done: int, total: int) -> str:
    if total == 0 or done >= total:
        return "green"
    if done == 0:
        return "red"
    return "yellow"


def _bar(done: int, total: int, width: int = 20) -> Text:
    filled = 0 if total == 0 else round(width * done / total)
    color = _pct_color(done, total)
    return Text("█" * filled, style=color) + Text("░" * (width - filled), style="grey37")


def render_terminal(
    result: ChecklistResult,
    *,
    show_missing: bool = True,
    console: Console | None = None,
) -> None:
    console = console or Console()

    header = (
        f"[bold]{result.player_name}[/bold]  "
        f"(on Level {result.current_level}, Mission {result.current_mission} · "
        f"{result.coins} coins)"
    )
    console.print(header)

    overall_color = _pct_color(result.overall_done, result.overall_total)
    console.print(
        f"[bold {overall_color}]Completion: {result.percent:.1f}%[/bold {overall_color}]"
        " [grey62](matches the in-game total)[/grey62]  "
        f"[grey62]· {result.overall_done}/{result.overall_total} collectibles[/grey62]\n"
    )

    summary = Table(show_header=True, header_style="bold")
    summary.add_column("Category")
    summary.add_column("Progress", justify="right")
    summary.add_column("")
    summary.add_column("%", justify="right")
    for cat in result.categories:
        pct = 0.0 if cat.total == 0 else 100.0 * cat.done / cat.total
        mark = "[green]✓[/green]" if cat.complete else " "
        summary.add_row(
            f"{mark} {cat.label}",
            f"{cat.done}/{cat.total}",
            _bar(cat.done, cat.total),
            f"[{_pct_color(cat.done, cat.total)}]{pct:.0f}%[/]",
        )
    console.print(summary)

    if not show_missing:
        return

    incomplete = [c for c in result.categories if not c.complete and c.missing]
    if not incomplete:
        console.print("\n[bold green]Everything is complete — 100%![/bold green]")
        return

    console.print("\n[bold]Remaining:[/bold]")
    for cat in incomplete:
        _print_missing(console, cat)


def _print_missing(console: Console, cat: CategoryResult) -> None:
    remaining = cat.total - cat.done
    console.print(f"\n[bold]{cat.label}[/bold] [grey62]({remaining} remaining)[/grey62]")
    for item in cat.missing:
        bullet = "•" if cat.named else "→"
        console.print(f"  [grey62]{bullet}[/grey62] {item}")
