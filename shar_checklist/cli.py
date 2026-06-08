"""Command-line entry point: ``shar-checklist <save.gci> [options]``."""

from __future__ import annotations

import argparse
import sys

from . import names
from .checklist import compute_checklist
from .errors import SharError
from .gci import read_gci
from .parser import parse_character_sheet
from .report import render_terminal, to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shar-checklist",
        description="Report Simpsons: Hit & Run 100% progress from a GameCube .gci save.",
    )
    parser.add_argument("save", help="path to the .gci save file")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a report")
    parser.add_argument(
        "--level", type=int, metavar="N", help="only show remaining items for level N (1-7)"
    )
    parser.add_argument(
        "--category",
        metavar="LIST",
        help="comma-separated category keys to show (e.g. cards,gags,story_missions)",
    )
    parser.add_argument(
        "--no-missing", action="store_true", help="show only the summary, not remaining items"
    )
    return parser


def _apply_filters(result, *, category: str | None, level: int | None):
    if category:
        wanted = {c.strip() for c in category.split(",") if c.strip()}
        valid_keys = {c.key for c in result.categories}
        unknown = wanted - valid_keys
        if unknown:
            raise SharError(
                f"unknown category: {', '.join(sorted(unknown))}. "
                f"valid: {', '.join(sorted(valid_keys))}"
            )
        result.categories = [c for c in result.categories if c.key in wanted]

    if level is not None:
        if not 1 <= level <= names.NUM_LEVELS:
            raise SharError(f"--level must be between 1 and {names.NUM_LEVELS}")
        prefix = names.LEVEL_LABELS[level - 1]
        for cat in result.categories:
            cat.missing = [m for m in cat.missing if m.startswith(prefix)]
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        save = parse_character_sheet(read_gci(args.save))
        result = compute_checklist(save)
        result = _apply_filters(result, category=args.category, level=args.level)
    except SharError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"error: file not found: {args.save}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(result))
    else:
        render_terminal(result, show_missing=not args.no_missing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
