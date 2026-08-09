from __future__ import annotations

import argparse
import shlex
from collections.abc import Callable

from .terminal import paint, print_panel


Handler = Callable[[argparse.Namespace], int]


def _choice(title: str, options: list[str], default: int | None = None) -> int:
    print()
    print(paint(title, "bold"))
    for index, option in enumerate(options, 1):
        marker = " *" if default == index else ""
        print(f"  {index}. {option}{marker}")
    while True:
        raw = input("Choose: ").strip()
        if not raw and default is not None:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw)
        print("Please enter one of the numbers shown above.")


def _yes_no(question: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{question} [{hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def _text(question: str, default: str = "") -> str:
    prompt = f"{question} [{default}]: " if default else f"{question}: "
    value = input(prompt).strip()
    return value or default


def _required_text(question: str) -> str:
    while True:
        value = input(f"{question}: ").strip()
        if value:
            return value
        print("Please enter a value.")


def _paths(question: str) -> list[str]:
    while True:
        raw = input(f"{question}: ").strip()
        if not raw:
            print("Enter at least one file or folder path.")
            continue
        try:
            values = shlex.split(raw)
        except ValueError as exc:
            print(f"Could not read those paths: {exc}")
            continue
        if values:
            return values


def _run_view(handler: Handler) -> int:
    path = _required_text("File path")
    tui = _yes_no("Use the full-screen viewer when possible?", True)
    summary = _yes_no("Show a summary too?", False)
    return handler(argparse.Namespace(path=path, tui=tui, summary=summary))


def _run_translate(handler: Handler) -> int:
    path = _required_text("File path")
    backend_index = _choice(
        "Translation backend",
        ["Automatic", "Translate Shell", "deep-translator", "LibreTranslate"],
        1,
    )
    backend = ["auto", "trans", "deep", "libre"][backend_index - 1]
    translate_keys = _yes_no("Translate object keys too?", False)
    output = _text("Output file, or leave blank to print") or None
    return handler(argparse.Namespace(path=path, backend=backend, keys=translate_keys, output=output))


def _run_emojify(handler: Handler) -> int:
    paths = _paths("Files or folders, separated by spaces")
    recursive = _yes_no("Include files inside subfolders?", False)
    apply = _yes_no("Actually rename the files now?", False)
    return handler(argparse.Namespace(paths=paths, recursive=recursive, apply=apply))


def _run_organize(handler: Handler) -> int:
    directory = _text("Folder to organize", ".")
    copy = _yes_no("Copy files instead of moving them?", False)
    no_emoji = not _yes_no("Add type-aware emoji to filenames?", True)
    apply = _yes_no("Actually organize the files now?", False)
    return handler(argparse.Namespace(directory=directory, copy=copy, no_emoji=no_emoji, apply=apply))


def run_wizard(handlers: dict[str, Handler]) -> int:
    print_panel(
        "View structured files, translate text, rename files with emoji, organize folders, and run diagnostics.",
        "✨ Magic Sorter X Wizard",
    )
    while True:
        selected = _choice(
            "What do you want to do?",
            [
                "View a file",
                "Translate a file to English",
                "Add emoji to filenames",
                "Organize a folder",
                "Run system checks",
                "Exit",
            ],
        )
        try:
            if selected == 1:
                code = _run_view(handlers["view"])
            elif selected == 2:
                code = _run_translate(handlers["translate"])
            elif selected == 3:
                code = _run_emojify(handlers["emojify"])
            elif selected == 4:
                code = _run_organize(handlers["organize"])
            elif selected == 5:
                code = handlers["doctor"](argparse.Namespace())
            else:
                print("Goodbye.")
                return 0
        except (EOFError, KeyboardInterrupt):
            print("\nWizard closed.")
            return 130
        if code:
            print(paint(f"That action finished with status {code}.", "yellow"))
        if not _yes_no("Do another action?", True):
            return code
