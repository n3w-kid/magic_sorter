from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .emojify import apply_plans, plan_emojify
from .models import Document, RenamePlan
from .organize import apply_organize, plan_organize
from .parsers import load_document, parse_text
from .render import render_document, render_summary
from .serialize import serialize
from .translation import (
    TranslationError,
    select_translator,
    translate_value,
    translate_xml_value,
)

console = Console()


def read_document(path: str | None) -> Document:
    if path and path != "-":
        return load_document(Path(path).expanduser())
    return parse_text(sys.stdin.read())


def print_plans(plans: list[RenamePlan], title: str) -> None:
    table = Table(title=title, show_lines=False)
    table.add_column("From", style="cyan", overflow="fold")
    table.add_column("To", style="green", overflow="fold")
    table.add_column("Why", style="magenta")
    for plan in plans:
        table.add_row(str(plan.source), str(plan.destination), plan.reason)
    console.print(table)


def command_view(args: argparse.Namespace) -> int:
    document = read_document(args.path)
    if args.tui and sys.stdout.isatty():
        try:
            from .tui import run_tui
            run_tui(document)
            return 0
        except Exception as exc:
            console.print(f"[yellow]TUI unavailable ({exc}); using rich preview.[/]")
    render_document(document)
    if args.summary:
        render_summary(document)
    return 0


def command_translate(args: argparse.Namespace) -> int:
    document = read_document(args.path)
    try:
        translator = select_translator(args.backend)
        console.print(f"[dim]🌐 Translation backend: {translator.name}[/]")
        translate_keys = args.keys
        if document.kind == "xml":
            if translate_keys:
                console.print(
                    "[yellow]XML element and attribute names are kept unchanged; "
                    "translating text nodes only.[/]"
                )
            translated = translate_xml_value(document.data, translator)
        else:
            translated = translate_value(document.data, translator, translate_keys)
    except TranslationError as exc:
        console.print(Panel(str(exc), title="❌ Translation unavailable", border_style="red"))
        return 2
    output = serialize(document.kind, translated)
    if args.output:
        destination = Path(args.output).expanduser()
        destination.write_text(output, encoding="utf-8")
        console.print(f"[green]✅ Wrote English translation to {destination}[/]")
    else:
        console.print(output, markup=False)
    return 0


def command_emojify(args: argparse.Namespace) -> int:
    plans = plan_emojify([Path(p).expanduser() for p in args.paths], args.recursive)
    if not plans:
        console.print("[green]✅ Nothing to rename.[/]")
        return 0
    print_plans(plans, "✨ Emoji rename plan")
    if not args.apply:
        console.print("[yellow]Dry run only. Add --apply to rename files.[/]")
        return 0
    apply_plans(plans)
    console.print(f"[green]✅ Renamed {len(plans)} file(s).[/]")
    return 0


def command_organize(args: argparse.Namespace) -> int:
    directory = Path(args.directory).expanduser().resolve()
    plans = plan_organize(directory, not args.no_emoji)
    if not plans:
        console.print("[green]✅ No loose files to organize.[/]")
        return 0
    print_plans(plans, "🧹 Organization plan")
    if not args.apply:
        console.print("[yellow]Dry run only. Add --apply to move/copy files.[/]")
        return 0
    apply_organize(plans, args.copy)
    console.print(f"[green]✅ Organized {len(plans)} file(s).[/]")
    return 0


def command_doctor(_: argparse.Namespace) -> int:
    checks: dict[str, Any] = {
        "Python": sys.version.split()[0],
        "Translate Shell (`trans`)": shutil.which("trans") or "not found",
        "Interactive terminal": sys.stdout.isatty(),
    }
    try:
        import deep_translator  # noqa: F401
        checks["deep-translator"] = "installed"
    except ImportError:
        checks["deep-translator"] = "not installed"
    console.print(Panel(json.dumps(checks, indent=2), title="🩺 Magic Sorter X doctor"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="msx",
        description="✨ View, translate, emojify, and organize files in the terminal.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    view = sub.add_parser("view", help="fx-like structured-data viewer")
    view.add_argument("path", nargs="?", help="file path, or read stdin")
    view.add_argument("--tui", action=argparse.BooleanOptionalAction, default=True)
    view.add_argument("--summary", action="store_true")
    view.set_defaults(func=command_view)

    translate = sub.add_parser("translate", help="auto-detect and translate strings to English")
    translate.add_argument("path", nargs="?", help="file path, or read stdin")
    translate.add_argument("-o", "--output")
    translate.add_argument("--backend", choices=["auto", "trans", "deep", "libre"], default="auto")
    translate.add_argument("--keys", action="store_true", help="also translate object keys")
    translate.set_defaults(func=command_translate)

    emojify = sub.add_parser("emojify", help="prefix filenames with type-aware emoji")
    emojify.add_argument("paths", nargs="+", help="files or directories")
    emojify.add_argument("-r", "--recursive", action="store_true")
    emojify.add_argument("--apply", action="store_true", help="perform changes; default is dry-run")
    emojify.set_defaults(func=command_emojify)

    organize = sub.add_parser("organize", help="sort loose files into emoji category folders")
    organize.add_argument("directory", nargs="?", default=".")
    organize.add_argument("--apply", action="store_true", help="perform changes; default is dry-run")
    organize.add_argument("--copy", action="store_true", help="copy instead of move")
    organize.add_argument("--no-emoji", action="store_true", help="keep original filenames")
    organize.set_defaults(func=command_organize)

    doctor = sub.add_parser("doctor", help="show optional-backend status")
    doctor.set_defaults(func=command_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, RuntimeError, ValueError) as exc:
        console.print(Panel(str(exc), title="❌ Error", border_style="red"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
