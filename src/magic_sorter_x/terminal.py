from __future__ import annotations

import os
import sys
from typing import Iterable


RESET = "\033[0m"
COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "dim": "\033[2m",
    "bold": "\033[1m",
}


def supports_color() -> bool:
    return sys.stdout.isatty() and os.getenv("NO_COLOR") is None


def paint(text: object, *styles: str) -> str:
    value = str(text)
    if not supports_color() or not styles:
        return value
    prefix = "".join(COLORS.get(style, "") for style in styles)
    return f"{prefix}{value}{RESET}"


def print_panel(text: str, title: str = "") -> None:
    lines = str(text).splitlines() or [""]
    width = max([len(title)] + [len(line) for line in lines])
    top = f"┌─ {title} " + "─" * max(0, width - len(title) + 1) + "┐" if title else "┌" + "─" * (width + 2) + "┐"
    print(top)
    for line in lines:
        print(f"│ {line.ljust(width)} │")
    print("└" + "─" * (width + 2) + "┘")


def print_table(headers: Iterable[str], rows: Iterable[Iterable[object]], title: str = "") -> None:
    header_list = [str(item) for item in headers]
    row_list = [[str(item) for item in row] for row in rows]
    widths = [len(item) for item in header_list]
    for row in row_list:
        for index, item in enumerate(row):
            if index >= len(widths):
                widths.append(len(item))
            else:
                widths[index] = max(widths[index], len(item))
    if title:
        print(paint(title, "bold"))
    print("  ".join(item.ljust(widths[index]) for index, item in enumerate(header_list)))
    print("  ".join("─" * width for width in widths))
    for row in row_list:
        print("  ".join((row[index] if index < len(row) else "").ljust(widths[index]) for index in range(len(widths))))
