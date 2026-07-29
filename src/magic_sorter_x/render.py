from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.pretty import Pretty
from rich.syntax import Syntax
from rich.tree import Tree

from .models import Document

console = Console()


def value_label(value: Any) -> str:
    if value is None:
        return "[bold magenta]null[/]"
    if isinstance(value, bool):
        return f"[bold magenta]{str(value).lower()}[/]"
    if isinstance(value, (int, float)):
        return f"[bold cyan]{value}[/]"
    if isinstance(value, str):
        preview = value if len(value) <= 100 else value[:97] + "…"
        return f"[green]{preview!r}[/]"
    return f"[dim]{type(value).__name__}[/]"


def add_tree(parent: Tree, value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            branch = parent.add(f"[bold blue]{key}[/] {value_label(child) if not isinstance(child, (dict, list)) else ''}")
            if isinstance(child, (dict, list)):
                add_tree(branch, child)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            branch = parent.add(f"[yellow][{index}][/] {value_label(child) if not isinstance(child, (dict, list)) else ''}")
            if isinstance(child, (dict, list)):
                add_tree(branch, child)


def render_document(document: Document) -> None:
    title = f"✨ Magic Sorter X · {document.kind.upper()}"
    if document.source:
        title += f" · {document.source.name}"

    if document.kind == "text":
        body = Syntax(str(document.data), "text", line_numbers=True, word_wrap=True)
    elif document.kind == "json":
        body = JSON(json.dumps(document.data, ensure_ascii=False))
    else:
        tree = Tree("[bold]🌳 document[/]")
        add_tree(tree, document.data)
        body = tree
    console.print(Panel(body, title=title, border_style="bright_blue", expand=False))


def render_summary(document: Document) -> None:
    value = document.data
    if isinstance(value, dict):
        stats = {"type": document.kind, "keys": len(value)}
    elif isinstance(value, list):
        stats = {"type": document.kind, "items": len(value)}
    else:
        stats = {"type": document.kind, "characters": len(str(value))}
    console.print(Panel(Pretty(stats), title="📊 Summary", border_style="green"))
