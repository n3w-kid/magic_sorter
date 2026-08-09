from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

from .models import Document

try:
    import curses
except ImportError:
    curses = None


@dataclass(slots=True, frozen=True)
class Node:
    path: tuple[str | int, ...]
    depth: int
    label: str
    value: Any

    @property
    def container(self) -> bool:
        return isinstance(self.value, (dict, list))


def preview(value: Any, width: int = 72) -> str:
    if isinstance(value, str):
        text = json.dumps(value, ensure_ascii=False)
    elif isinstance(value, dict):
        text = f"{{{len(value)} keys}}"
    elif isinstance(value, list):
        text = f"[{len(value)} items]"
    else:
        text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= width else text[: max(1, width - 1)] + "…"


def children(value: Any) -> Iterable[tuple[str | int, Any]]:
    if isinstance(value, dict):
        yield from value.items()
    elif isinstance(value, list):
        yield from enumerate(value)


def all_container_paths(value: Any, path: tuple[str | int, ...] = ()) -> set[tuple[str | int, ...]]:
    result: set[tuple[str | int, ...]] = set()
    if isinstance(value, (dict, list)):
        result.add(path)
        for key, child in children(value):
            result.update(all_container_paths(child, path + (key,)))
    return result


def matches(node: Node, query: str) -> bool:
    if not query:
        return True
    haystack = f"{node.label} {preview(node.value, 300)} {'/'.join(map(str, node.path))}".casefold()
    return query.casefold() in haystack


def visible_nodes(value: Any, expanded: set[tuple[str | int, ...]], query: str = "") -> list[Node]:
    output: list[Node] = []

    def walk(current: Any, path: tuple[str | int, ...], depth: int, label: str) -> bool:
        node = Node(path, depth, label, current)
        descendants: list[Node] = []
        descendant_match = False
        if node.container and (path in expanded or query):
            before = len(output)
            for key, child in children(current):
                child_label = f"[{key}]" if isinstance(key, int) else str(key)
                if walk(child, path + (key,), depth + 1, child_label):
                    descendant_match = True
            descendants = output[before:]
            del output[before:]
        self_match = matches(node, query)
        include = not query or self_match or descendant_match
        if include:
            output.append(node)
            output.extend(descendants)
        return self_match or descendant_match

    walk(value, (), 0, "document")
    return output


def format_path(path: tuple[str | int, ...]) -> str:
    if not path:
        return "$"
    parts = ["$"]
    for item in path:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        elif item.isidentifier():
            parts.append(f".{item}")
        else:
            parts.append(f"[{json.dumps(item, ensure_ascii=False)}]")
    return "".join(parts)


class CursesViewer:
    def __init__(self, document: Document) -> None:
        if curses is None:
            raise RuntimeError("Full-screen TUI is not available in this Python build")
        self.document = document
        self.expanded: set[tuple[str | int, ...]] = {()}
        self.query = ""
        self.index = 0
        self.offset = 0
        self.message = "Enter/Space toggle · / search · e expand · c collapse · q quit"

    def run(self) -> None:
        curses.wrapper(self._main)

    def _main(self, screen: Any) -> None:
        curses.curs_set(0)
        screen.keypad(True)
        try:
            curses.use_default_colors()
        except curses.error:
            pass
        while True:
            nodes = visible_nodes(self.document.data, self.expanded, self.query)
            if not nodes:
                nodes = [Node((), 0, "No matches", self.document.data)]
            self.index = max(0, min(self.index, len(nodes) - 1))
            self._draw(screen, nodes)
            key = screen.getch()
            if key in (ord("q"), 27):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                self.index = min(len(nodes) - 1, self.index + 1)
            elif key in (curses.KEY_UP, ord("k")):
                self.index = max(0, self.index - 1)
            elif key == curses.KEY_NPAGE:
                self.index = min(len(nodes) - 1, self.index + max(1, screen.getmaxyx()[0] - 5))
            elif key == curses.KEY_PPAGE:
                self.index = max(0, self.index - max(1, screen.getmaxyx()[0] - 5))
            elif key in (10, 13, ord(" "), curses.KEY_RIGHT, ord("l")):
                node = nodes[self.index]
                if node.container:
                    if node.path in self.expanded:
                        self.expanded.remove(node.path)
                    else:
                        self.expanded.add(node.path)
            elif key in (curses.KEY_LEFT, ord("h")):
                node = nodes[self.index]
                if node.path in self.expanded:
                    self.expanded.remove(node.path)
                elif node.path:
                    parent = node.path[:-1]
                    for position, candidate in enumerate(nodes):
                        if candidate.path == parent:
                            self.index = position
                            break
            elif key == ord("e"):
                self.expanded = all_container_paths(self.document.data)
                self.message = f"Expanded {len(self.expanded)} containers"
            elif key == ord("c"):
                self.expanded = {()}
                self.index = 0
                self.message = "Collapsed tree"
            elif key == ord("/"):
                self.query = self._prompt(screen, "Search: ")
                self.index = 0
                self.message = f"Search: {self.query}" if self.query else "Search cleared"
            elif key == ord("n") and self.query:
                self.index = min(len(nodes) - 1, self.index + 1)

    def _prompt(self, screen: Any, label: str) -> str:
        height, width = screen.getmaxyx()
        curses.curs_set(1)
        screen.move(height - 1, 0)
        screen.clrtoeol()
        screen.addnstr(height - 1, 0, label, max(0, width - 1))
        screen.refresh()
        try:
            raw = screen.getstr(height - 1, min(len(label), width - 1), max(1, width - len(label) - 1))
            return raw.decode("utf-8", errors="replace").strip()
        finally:
            curses.curs_set(0)

    def _draw(self, screen: Any, nodes: list[Node]) -> None:
        screen.erase()
        height, width = screen.getmaxyx()
        source = self.document.source.name if self.document.source else "stdin"
        header = f"✨ Magic Sorter X · {self.document.kind.upper()} · {source}"
        screen.addnstr(0, 0, header, max(0, width - 1), curses.A_BOLD)
        screen.addnstr(1, 0, f"🔎 {self.query}" if self.query else self.message, max(0, width - 1), curses.A_BOLD if self.query else curses.A_NORMAL)
        body_height = max(1, height - 4)
        if self.index < self.offset:
            self.offset = self.index
        elif self.index >= self.offset + body_height:
            self.offset = self.index - body_height + 1
        for row, node in enumerate(nodes[self.offset:self.offset + body_height], start=2):
            absolute = self.offset + row - 2
            marker = "▼" if node.container and node.path in self.expanded else "▶" if node.container else "•"
            indent = "  " * node.depth
            line = f"{indent}{marker} {node.label}: {preview(node.value, max(10, width - len(indent) - 8))}"
            attr = curses.A_REVERSE if absolute == self.index else curses.A_NORMAL
            try:
                screen.addnstr(row, 0, line, max(0, width - 1), attr)
            except curses.error:
                pass
        selected = nodes[self.index]
        footer = f"{format_path(selected.path)} · {self.index + 1}/{len(nodes)}"
        try:
            screen.addnstr(height - 1, 0, footer, max(0, width - 1), curses.A_DIM)
        except curses.error:
            pass
        screen.refresh()


def run_tui(document: Document) -> None:
    CursesViewer(document).run()
