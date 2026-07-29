from __future__ import annotations

import csv
import io
import json
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .models import Document

_JSON_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def _strip_json_comments(text: str) -> str:
    """Remove // and /* */ comments without touching comment markers in strings."""
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == "/" and nxt == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and nxt == "*":
            index += 2
            while index + 1 < len(text) and text[index:index + 2] != "*/":
                index += 1
            index += 2 if index + 1 < len(text) else 0
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _relaxed_json(text: str) -> Any:
    """Parse JSON while tolerating comments and trailing commas."""
    cleaned = _strip_json_comments(text)
    cleaned = _JSON_TRAILING_COMMA.sub(r"\1", cleaned)
    return json.loads(cleaned)


def _xml_value(element: ET.Element) -> Any:
    """Convert one XML element to a JSON-like value without duplicating its tag."""
    node: dict[str, Any] = {}
    if element.attrib:
        node["@attributes"] = dict(element.attrib)

    text = (element.text or "").strip()
    children: dict[str, list[Any]] = {}
    for child in element:
        children.setdefault(child.tag, []).append(_xml_value(child))
    for tag, values in children.items():
        node[tag] = values[0] if len(values) == 1 else values

    if node:
        if text:
            node["#text"] = text
        return node
    return text or None


def _xml_to_data(element: ET.Element) -> dict[str, Any]:
    return {element.tag: _xml_value(element)}


def _parse_csv(text: str) -> list[dict[str, str]]:
    sample = text[:4096]
    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise ValueError("CSV has no header")
    return list(reader)


def parse_text(text: str, source: Path | None = None) -> Document:
    stripped = text.lstrip("\ufeff").strip()
    if not stripped:
        return Document(source, "text", "", text)

    suffix = source.suffix.lower() if source else ""
    attempts: list[tuple[str, Any]] = []

    if suffix in {".json", ".jsonc", ".jsonl", ".ndjson"} or stripped[:1] in "[{":
        if suffix in {".jsonl", ".ndjson"}:
            attempts.append(("jsonl", lambda: [_relaxed_json(line) for line in stripped.splitlines() if line.strip()]))
        attempts.append(("json", lambda: _relaxed_json(stripped)))

    if suffix == ".toml":
        attempts.append(("toml", lambda: tomllib.loads(stripped)))

    if suffix in {".xml", ".svg"} or stripped.startswith("<"):
        attempts.append(("xml", lambda: _xml_to_data(ET.fromstring(stripped))))

    if suffix in {".yaml", ".yml"} or ":" in stripped:
        def parse_yaml() -> Any:
            import yaml  # optional at import time
            return yaml.safe_load(stripped)
        attempts.append(("yaml", parse_yaml))

    if suffix in {".csv", ".tsv"} or any(d in stripped.splitlines()[0] for d in [",", ";", "\t", "|"]):
        attempts.append(("csv", lambda: _parse_csv(stripped)))

    seen: set[str] = set()
    for kind, parser in attempts:
        if kind in seen:
            continue
        seen.add(kind)
        try:
            value = parser()
            if value is not None:
                return Document(source, kind, value, text)
        except (ValueError, TypeError, ET.ParseError, json.JSONDecodeError, csv.Error, ImportError):
            continue
        except Exception:
            # Third-party parsers (notably YAML) use their own exception hierarchy.
            continue

    return Document(source, "text", stripped, text)


def load_document(path: Path) -> Document:
    return parse_text(path.read_text(encoding="utf-8-sig"), path)
