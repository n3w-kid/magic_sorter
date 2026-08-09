from __future__ import annotations

import json
from typing import Any

from .models import Document
from .terminal import paint, print_panel


def value_label(value: Any) -> str:
    if value is None:
        return paint("null", "magenta", "bold")
    if isinstance(value, bool):
        return paint(str(value).lower(), "magenta", "bold")
    if isinstance(value, (int, float)):
        return paint(value, "cyan", "bold")
    if isinstance(value, str):
        preview = value if len(value) <= 100 else value[:97] + "…"
        return paint(repr(preview), "green")
    return paint(type(value).__name__, "dim")


def _tree_lines(value: Any, prefix: str = "", label: str = "document") -> list[str]:
    lines: list[str] = []
    if isinstance(value, dict):
        lines.append(f"{prefix}{paint(label, 'blue', 'bold')} {paint('{' + str(len(value)) + ' keys}', 'dim')}")
        items = list(value.items())
        for index, (key, child) in enumerate(items):
            connector = "└─" if index == len(items) - 1 else "├─"
            next_prefix = prefix + ("  " if index == len(items) - 1 else "│ ")
            if isinstance(child, (dict, list)):
                nested = _tree_lines(child, next_prefix, str(key))
                first = nested.pop(0)
                lines.append(f"{prefix}{connector} {first[len(next_prefix):]}")
                lines.extend(nested)
            else:
                lines.append(f"{prefix}{connector} {paint(key, 'blue', 'bold')}: {value_label(child)}")
        return lines
    if isinstance(value, list):
        lines.append(f"{prefix}{paint(label, 'yellow', 'bold')} {paint('[' + str(len(value)) + ' items]', 'dim')}")
        for index, child in enumerate(value):
            connector = "└─" if index == len(value) - 1 else "├─"
            next_prefix = prefix + ("  " if index == len(value) - 1 else "│ ")
            if isinstance(child, (dict, list)):
                nested = _tree_lines(child, next_prefix, f"[{index}]")
                first = nested.pop(0)
                lines.append(f"{prefix}{connector} {first[len(next_prefix):]}")
                lines.extend(nested)
            else:
                lines.append(f"{prefix}{connector} {paint('[' + str(index) + ']', 'yellow')}: {value_label(child)}")
        return lines
    return [f"{prefix}{label}: {value_label(value)}"]


def render_document(document: Document) -> None:
    title = f"✨ Magic Sorter X · {document.kind.upper()}"
    if document.source:
        title += f" · {document.source.name}"
    if document.kind == "text":
        body = "\n".join(f"{index:>4} │ {line}" for index, line in enumerate(str(document.data).splitlines(), 1))
    elif document.kind == "json":
        body = json.dumps(document.data, ensure_ascii=False, indent=2)
    else:
        body = "\n".join(_tree_lines(document.data))
    print_panel(body, title)


def render_summary(document: Document) -> None:
    value = document.data
    if isinstance(value, dict):
        stats = {"type": document.kind, "keys": len(value)}
    elif isinstance(value, list):
        stats = {"type": document.kind, "items": len(value)}
    else:
        stats = {"type": document.kind, "characters": len(str(value))}
    print_panel(json.dumps(stats, indent=2), "📊 Summary")
