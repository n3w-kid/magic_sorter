from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from typing import Any


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


def serialize(kind: str, data: Any) -> str:
    if kind in {"json", "jsonl"}:
        if kind == "jsonl" and isinstance(data, list):
            return "\n".join(json.dumps(item, ensure_ascii=False) for item in data) + "\n"
        return json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if kind in {"yaml", "yml"}:
        import yaml
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    if kind == "toml":
        try:
            import tomli_w
        except ImportError as exc:
            raise RuntimeError("TOML writing needs `pip install tomli-w`") from exc
        return tomli_w.dumps(data)
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
