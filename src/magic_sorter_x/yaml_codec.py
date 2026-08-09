from __future__ import annotations

import json
import re
from typing import Any


_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def _strip_comment(line: str) -> str:
    single = False
    double = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and double:
            escaped = True
            continue
        if char == "'" and not double:
            single = not single
            continue
        if char == '"' and not single:
            double = not double
            continue
        if char == "#" and not single and not double and (index == 0 or line[index - 1].isspace()):
            return line[:index].rstrip()
    return line.rstrip()


def _split_key_value(text: str) -> tuple[str, str] | None:
    single = False
    double = False
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\" and double:
            escaped = True
            continue
        if char == "'" and not double:
            single = not single
            continue
        if char == '"' and not single:
            double = not double
            continue
        if char == ":" and not single and not double:
            key = text[:index].strip()
            if key:
                return key, text[index + 1:].strip()
    return None


def _scalar(text: str) -> Any:
    value = text.strip()
    if not value:
        return None
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            return value
    if value.startswith("{") and value.endswith("}"):
        try:
            return json.loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            return value
    if _NUMBER.match(value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    return value


def loads(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        cleaned = _strip_comment(raw.expandtabs(2))
        if not cleaned.strip() or cleaned.lstrip().startswith("---") or cleaned.lstrip().startswith("..."):
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        lines.append((indent, cleaned.strip()))
    if not lines:
        return None

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        is_list = lines[index][0] == indent and lines[index][1].startswith("-")
        container: Any = [] if is_list else {}
        while index < len(lines):
            line_indent, content = lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                raise ValueError(f"Unexpected indentation near: {content}")
            if is_list:
                if not content.startswith("-"):
                    break
                item_text = content[1:].strip()
                if not item_text:
                    if index + 1 >= len(lines) or lines[index + 1][0] <= indent:
                        container.append(None)
                        index += 1
                    else:
                        item, index = parse_block(index + 1, lines[index + 1][0])
                        container.append(item)
                    continue
                pair = _split_key_value(item_text)
                if pair:
                    key, raw_value = pair
                    item_map: dict[str, Any] = {}
                    if raw_value:
                        item_map[str(_scalar(key))] = _scalar(raw_value)
                        index += 1
                    elif index + 1 < len(lines) and lines[index + 1][0] > indent:
                        child, index = parse_block(index + 1, lines[index + 1][0])
                        item_map[str(_scalar(key))] = child
                    else:
                        item_map[str(_scalar(key))] = None
                        index += 1
                    while index < len(lines) and lines[index][0] > indent:
                        child_indent, child_content = lines[index]
                        child_pair = _split_key_value(child_content)
                        if child_pair is None:
                            break
                        child_key, child_raw = child_pair
                        if child_raw:
                            item_map[str(_scalar(child_key))] = _scalar(child_raw)
                            index += 1
                        elif index + 1 < len(lines) and lines[index + 1][0] > child_indent:
                            child_value, index = parse_block(index + 1, lines[index + 1][0])
                            item_map[str(_scalar(child_key))] = child_value
                        else:
                            item_map[str(_scalar(child_key))] = None
                            index += 1
                    container.append(item_map)
                else:
                    container.append(_scalar(item_text))
                    index += 1
                continue
            pair = _split_key_value(content)
            if pair is None:
                raise ValueError(f"Expected key/value pair near: {content}")
            key, raw_value = pair
            key_text = str(_scalar(key))
            if raw_value:
                container[key_text] = _scalar(raw_value)
                index += 1
            elif index + 1 < len(lines) and lines[index + 1][0] > indent:
                child, index = parse_block(index + 1, lines[index + 1][0])
                container[key_text] = child
            else:
                container[key_text] = None
                index += 1
        return container, index

    value, position = parse_block(0, lines[0][0])
    if position != len(lines):
        raise ValueError("Could not parse the complete YAML document")
    return value


def _needs_quotes(text: str) -> bool:
    lowered = text.lower()
    if lowered in {"", "null", "true", "false", "yes", "no", "on", "off", "~"}:
        return True
    if text[0] in "-?:,[]{}#&*!|>'\"%@`" or text[-1].isspace() or text[0].isspace():
        return True
    if ": " in text or " #" in text or "\n" in text or _NUMBER.match(text):
        return True
    return False


def _dump_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    return json.dumps(text, ensure_ascii=False) if _needs_quotes(text) else text


def dumps(data: Any) -> str:
    lines: list[str] = []

    def emit(value: Any, indent: int, key: str | None = None) -> None:
        prefix = " " * indent
        if key is not None:
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                for child_key, child_value in value.items():
                    emit(child_value, indent + 2, str(child_key))
                return
            if isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                emit(value, indent + 2)
                return
            lines.append(f"{prefix}{key}: {_dump_scalar(value)}")
            return
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    if not item:
                        lines.append(f"{prefix}- {{}}")
                        continue
                    first = True
                    for child_key, child_value in item.items():
                        if first and not isinstance(child_value, (dict, list)):
                            lines.append(f"{prefix}- {child_key}: {_dump_scalar(child_value)}")
                            first = False
                        else:
                            if first:
                                lines.append(f"{prefix}-")
                                first = False
                                emit(child_value, indent + 2, str(child_key))
                            else:
                                emit(child_value, indent + 2, str(child_key))
                elif isinstance(item, list):
                    lines.append(f"{prefix}-")
                    emit(item, indent + 2)
                else:
                    lines.append(f"{prefix}- {_dump_scalar(item)}")
            return
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                emit(child_value, indent, str(child_key))
            return
        lines.append(f"{prefix}{_dump_scalar(value)}")

    emit(data, 0)
    return "\n".join(lines) + ("\n" if lines else "")
