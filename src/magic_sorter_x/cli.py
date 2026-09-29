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
from .godot_text import (
    export_editable_text,
    find_gdre_tools,
    import_edited_text,
    list_godot_pack_files,
    patch_godot_pack,
    recover_godot_scripts,
)
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



def command_godot_export(args: argparse.Namespace) -> int:
    source = Path(args.path).expanduser().resolve()
    output = Path(args.output).expanduser() if args.output else source.with_name(source.stem + ".msx.txt")
    count = export_editable_text(source, output, args.overwrite)
    print(paint(f"✅ Exported {count} GDScript string(s) to {output.resolve()}", "green"))
    print(paint("Edit only the lines beginning with | and keep the @@MSX marker lines unchanged.", "dim"))
    return 0


def command_godot_import(args: argparse.Namespace) -> int:
    source = Path(args.path).expanduser().resolve()
    edited = Path(args.edited).expanduser().resolve()
    output = Path(args.output).expanduser() if args.output else source.with_name(source.stem + "_patched.gd")
    result = import_edited_text(source, edited, output, args.overwrite)
    print(
        paint(
            f"✅ Wrote {output.resolve()} ({result.changed_blocks} changed, "
            f"{result.matched_blocks} matched block(s)).",
            "green",
        )
    )
    return 0


def command_godot_list(args: argparse.Namespace) -> int:
    return list_godot_pack_files(Path(args.game), args.gdre)


def command_godot_recover(args: argparse.Namespace) -> int:
    game = Path(args.game).expanduser().resolve()
    output = Path(args.output).expanduser() if args.output else game.with_name(game.stem + "_recovered")
    code = recover_godot_scripts(game, output, args.gdre, args.include)
    if code == 0:
        print(paint(f"✅ Recovered Godot scripts to {output.resolve()}", "green"))
    return code


def command_godot_patch(args: argparse.Namespace) -> int:
    game = Path(args.game).expanduser().resolve()
    source = Path(args.source).expanduser().resolve()
    output = (
        Path(args.output).expanduser()
        if args.output
        else game.with_name(game.stem + "_patched" + game.suffix)
    )
    code = patch_godot_pack(
        game,
        source,
        args.dest,
        output,
        gdre=args.gdre,
        bytecode=args.bytecode,
    )
    if code == 0:
        print(paint(f"✅ Patched output written to {output.resolve()}", "green"))
    return code


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
    try:
        checks["GDRE Tools"] = str(find_gdre_tools())
    except RuntimeError:
        checks["GDRE Tools"] = "not found (only needed for PCK/EXE recovery or patching)"
    print_panel(json.dumps(checks, indent=2), "🩺 Magic Sorter X doctor")
    return 0


def command_wizard(_: argparse.Namespace | None = None) -> int:
    from .wizard import run_wizard
    return run_wizard(
        {
            "view": command_view,
            "translate": command_translate,
            "godot_export": command_godot_export,
            "godot_import": command_godot_import,
            "godot_list": command_godot_list,
            "godot_recover": command_godot_recover,
            "godot_patch": command_godot_patch,
            "emojify": command_emojify,
            "organize": command_organize,
            "doctor": command_doctor,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="msx",
        description="✨ View, translate, edit Godot text, emojify, and organize files from one command.",
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

    godot_export = sub.add_parser("godot-export", help="extract string variables from a .gd file to editable text")
    godot_export.add_argument("path", help="source .gd file")
    godot_export.add_argument("-o", "--output")
    godot_export.add_argument("--overwrite", action="store_true")
    godot_export.set_defaults(func=command_godot_export)

    godot_import = sub.add_parser("godot-import", help="merge edited text back into a copy of a .gd file")
    godot_import.add_argument("path", help="original .gd file")
    godot_import.add_argument("edited", help="editable text file created by godot-export")
    godot_import.add_argument("-o", "--output")
    godot_import.add_argument("--overwrite", action="store_true")
    godot_import.set_defaults(func=command_godot_import)

    godot_list = sub.add_parser("godot-list", help="list files inside a Godot PCK/EXE/APK using GDRE Tools")
    godot_list.add_argument("game", help="game PCK, EXE, or APK")
    godot_list.add_argument("--gdre", help="path to gdre_tools executable")
    godot_list.set_defaults(func=command_godot_list)

    godot_recover = sub.add_parser("godot-recover", help="recover/decompile scripts from a Godot game package")
    godot_recover.add_argument("game", help="game PCK, EXE, or APK")
    godot_recover.add_argument("-o", "--output", help="recovery folder")
    godot_recover.add_argument("--include", help="optional GDRE include glob, e.g. res://**/questtext.gdc")
    godot_recover.add_argument("--gdre", help="path to gdre_tools executable")
    godot_recover.set_defaults(func=command_godot_recover)

    godot_patch = sub.add_parser("godot-patch", help="patch an edited .gd/.gdc file into a new PCK/EXE")
    godot_patch.add_argument("game", help="original game PCK or EXE")
    godot_patch.add_argument("source", help="edited .gd or compiled .gdc file")
    godot_patch.add_argument("--dest", required=True, help="exact destination, e.g. res://scripts/questtext.gd")
    godot_patch.add_argument("-o", "--output", help="new patched PCK/EXE path")
    godot_patch.add_argument("--bytecode", help="Godot/bytecode version when .gd must be compiled to .gdc")
    godot_patch.add_argument("--gdre", help="path to gdre_tools executable")
    godot_patch.set_defaults(func=command_godot_patch)

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
        # Always open the wizard when no command is supplied. This is important
        # for IDE consoles such as Thonny, where stdin is often not reported as a TTY.
        return command_wizard(args)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 130
    except (OSError, RuntimeError, ValueError) as exc:
        print_panel(str(exc), "❌ Error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
