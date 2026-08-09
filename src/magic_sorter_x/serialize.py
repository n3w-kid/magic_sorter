from __future__ import annotations

import csv
import datetime as dt
import io
import json
import xml.etree.ElementTree as ET
from typing import Any

from .yaml_codec import dumps as yaml_dumps


def _xml_element(tag: str, value: Any) -> ET.Element:
    element = ET.Element(tag)
    if value is None:
        return element
    if not isinstance(value, dict):
        element.text = str(value)
        return element
    attributes = value.get("@attributes", {})
    if isinstance(attributes, dict):
        for key, attribute_value in attributes.items():
            element.set(str(key), str(attribute_value))
    if "#text" in value and value["#text"] is not None:
        element.text = str(value["#text"])
    for child_tag, child_value in value.items():
        if child_tag in {"@attributes", "#text"}:
            continue
        if isinstance(child_value, list):
            for item in child_value:
                element.append(_xml_element(str(child_tag), item))
        else:
            element.append(_xml_element(str(child_tag), child_value))
    return element


def _serialize_xml(data: Any) -> str:
    if not isinstance(data, dict) or len(data) != 1:
        raise RuntimeError("XML data must have exactly one root element")
    root_tag, root_value = next(iter(data.items()))
    root = _xml_element(str(root_tag), root_value)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def _toml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, list) and all(not isinstance(item, dict) for item in value):
        return "[" + ", ".join(_toml_scalar(item) for item in value) + "]"
    raise RuntimeError(f"Unsupported TOML value: {type(value).__name__}")


def _serialize_toml(data: Any) -> str:
    if not isinstance(data, dict):
        raise RuntimeError("TOML data must be a table")
    lines: list[str] = []

    def emit_table(table: dict[str, Any], path: tuple[str, ...], write_header: bool) -> None:
        if write_header:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append("[" + ".".join(path) + "]")
        nested: list[tuple[str, dict[str, Any]]] = []
        arrays: list[tuple[str, list[dict[str, Any]]]] = []
        for key, value in table.items():
            if isinstance(value, dict):
                nested.append((str(key), value))
            elif isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                arrays.append((str(key), value))
            else:
                lines.append(f"{key} = {_toml_scalar(value)}")
        for key, value in nested:
            emit_table(value, path + (key,), True)
        for key, values in arrays:
            for item in values:
                if lines and lines[-1] != "":
                    lines.append("")
                section = path + (key,)
                lines.append("[[" + ".".join(section) + "]]" )
                scalar_items = {k: v for k, v in item.items() if not isinstance(v, dict)}
                nested_items = {k: v for k, v in item.items() if isinstance(v, dict)}
                for item_key, item_value in scalar_items.items():
                    lines.append(f"{item_key} = {_toml_scalar(item_value)}")
                for item_key, item_value in nested_items.items():
                    emit_table(item_value, section + (str(item_key),), True)

    emit_table(data, (), False)
    return "\n".join(lines).rstrip() + "\n"


def serialize(kind: str, data: Any) -> str:
    if kind in {"json", "jsonl"}:
        if kind == "jsonl" and isinstance(data, list):
            return "\n".join(json.dumps(item, ensure_ascii=False) for item in data) + "\n"
        return json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if kind in {"yaml", "yml"}:
        try:
            import yaml
        except ImportError:
            return yaml_dumps(data)
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    if kind == "toml":
        return _serialize_toml(data)
    if kind == "xml":
        return _serialize_xml(data)
    if kind == "csv" and isinstance(data, list) and (not data or isinstance(data[0], dict)):
        if not data:
            return ""
        fieldnames: list[str] = []
        for row in data:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    return str(data)
