from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .emojify import apply_plans, plan_emojify
from .models import Document, RenamePlan
from .organize import apply_organize, plan_organize
from .parsers import load_document, parse_text
from .render import render_document, render_summary
from .serialize import serialize
from .terminal import paint, print_panel, print_table
from .translation import TranslationError, select_translator, translate_value, translate_xml_value


def read_document(path: str | None) -> Document:
    if path and path != "-":
        return load_document(Path(path).expanduser())
    return parse_text(sys.stdin.read())


def print_plans(plans: list[RenamePlan], title: str) -> None:
    rows = [(plan.source, plan.destination, plan.reason) for plan in plans]
    print_table(["From", "To", "Why"], rows, title)


def command_view(args: argparse.Namespace) -> int:
    document = read_document(args.path)
    if args.tui and sys.stdout.isatty():
        try:
            from .tui import run_tui
            run_tui(document)
            return 0
        except Exception as exc:
            print(paint(f"TUI unavailable ({exc}); using normal preview.", "yellow"))
    render_document(document)
    if args.summary:
        render_summary(document)
    return 0


def command_translate(args: argparse.Namespace) -> int:
    document = read_document(args.path)
    try:
        translator = select_translator(args.backend)
        print(paint(f"🌐 Translation backend: {translator.name}", "dim"))
        if document.kind == "xml":
            if args.keys:
                print(paint("XML element and attribute names stay unchanged; only text nodes are translated.", "yellow"))
            translated = translate_xml_value(document.data, translator)
        else:
            translated = translate_value(document.data, translator, args.keys)
    except TranslationError as exc:
        print_panel(str(exc), "❌ Translation unavailable")
        return 2
    output = serialize(document.kind, translated)
    if args.output:
        destination = Path(args.output).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output, encoding="utf-8")
        print(paint(f"✅ Wrote English translation to {destination}", "green"))
    else:
        print(output, end="" if output.endswith("\n") else "\n")
    return 0


def command_emojify(args: argparse.Namespace) -> int:
    plans = plan_emojify([Path(path).expanduser() for path in args.paths], args.recursive)
    if not plans:
        print(paint("✅ Nothing to rename.", "green"))
        return 0
    print_plans(plans, "✨ Emoji rename plan")
    if not args.apply:
        print(paint("Dry run only. Use --apply when you want to rename the files.", "yellow"))
        return 0
    apply_plans(plans)
    print(paint(f"✅ Renamed {len(plans)} file(s).", "green"))
    return 0


def command_organize(args: argparse.Namespace) -> int:
    directory = Path(args.directory).expanduser().resolve()
    plans = plan_organize(directory, not args.no_emoji)
    if not plans:
        print(paint("✅ No loose files to organize.", "green"))
        return 0
    print_plans(plans, "🧹 Organization plan")
    if not args.apply:
        print(paint("Dry run only. Use --apply when you want to move or copy the files.", "yellow"))
        return 0
    apply_organize(plans, args.copy)
    print(paint(f"✅ Organized {len(plans)} file(s).", "green"))
    return 0


def command_doctor(_: argparse.Namespace) -> int:
    checks: dict[str, Any] = {
        "Python": sys.version.split()[0],
        "Project mode": "direct run",
        "Translate Shell (trans)": shutil.which("trans") or "not found",
        "LibreTranslate URL": os.getenv("LIBRETRANSLATE_URL") or "not configured",
        "Interactive terminal": sys.stdout.isatty(),
    }
    try:
        import deep_translator
        checks["deep-translator"] = "available" if deep_translator else "not available"
    except ImportError:
        checks["deep-translator"] = "not available"
    print_panel(json.dumps(checks, indent=2), "🩺 Magic Sorter X doctor")
    return 0


def command_wizard(_: argparse.Namespace | None = None) -> int:
    from .wizard import run_wizard
    return run_wizard(
        {
            "view": command_view,
            "translate": command_translate,
            "emojify": command_emojify,
            "organize": command_organize,
            "doctor": command_doctor,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="msx",
        description="✨ View, translate, emojify, and organize files from one command.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-w", "--wizard", action="store_true", help="open the guided wizard")
    sub = parser.add_subparsers(dest="command")

    view = sub.add_parser("view", help="open the structured-data viewer")
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

    doctor = sub.add_parser("doctor", help="show translation and terminal status")
    doctor.set_defaults(func=command_doctor)

    wizard = sub.add_parser("wizard", help="open the guided wizard")
    wizard.set_defaults(func=command_wizard)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.wizard:
            return command_wizard(args)
        if hasattr(args, "func"):
            return int(args.func(args))
        if sys.stdin.isatty():
            return command_wizard(args)
        return command_view(argparse.Namespace(path=None, tui=False, summary=False))
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 130
    except (OSError, RuntimeError, ValueError) as exc:
        print_panel(str(exc), "❌ Error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
