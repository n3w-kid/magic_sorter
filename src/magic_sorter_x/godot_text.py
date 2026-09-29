from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


_ASSIGNMENT = re.compile(
    r"(?m)^[ \t]*(?:@[A-Za-z_]\w*(?:\([^()\n]*\))?[ \t]+)*"
    r"(?:static[ \t]+)?(?:var|const)\s+(?P<name>[A-Za-z_]\w*)"
    r"(?:\s*:\s*[^=\n]+)?\s*=\s*"
)
_BEGIN = re.compile(r"^@@MSX:BEGIN\s+(?P<index>\d+)\s+(?P<name>[A-Za-z_]\w*)$")
_END = re.compile(r"^@@MSX:END\s+(?P<index>\d+)$")


@dataclass(frozen=True)
class GodotString:
    index: int
    name: str
    value: str
    literal_start: int
    literal_end: int


@dataclass(frozen=True)
class MergeResult:
    total_blocks: int
    matched_blocks: int
    changed_blocks: int
    output_text: str


_UTF8_BOM = b"\xef\xbb\xbf"


def _read_utf8_preserve(path: Path) -> tuple[str, bool]:
    data = path.read_bytes()
    has_bom = data.startswith(_UTF8_BOM)
    if has_bom:
        data = data[len(_UTF8_BOM):]
    return data.decode("utf-8"), has_bom


def _write_utf8_preserve(path: Path, text: str, bom: bool = False) -> None:
    data = text.encode("utf-8")
    if bom:
        data = _UTF8_BOM + data
    path.write_bytes(data)


def _scan_string_literal(text: str, start: int) -> int | None:
    if start >= len(text) or text[start] not in {"'", '"'}:
        return None
    quote = text[start]
    triple = text.startswith(quote * 3, start)
    delimiter = quote * 3 if triple else quote
    i = start + len(delimiter)
    while i < len(text):
        if text.startswith(delimiter, i):
            return i + len(delimiter)
        if text[i] == "\\":
            i += 2
        else:
            i += 1
    return None


def _decode_escape(content: str) -> str:
    output: list[str] = []
    i = 0
    simple = {
        "a": "\a",
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "v": "\v",
        "\\": "\\",
        '"': '"',
        "'": "'",
    }
    while i < len(content):
        char = content[i]
        if char != "\\" or i + 1 >= len(content):
            output.append(char)
            i += 1
            continue
        esc = content[i + 1]
        if esc in simple:
            output.append(simple[esc])
            i += 2
            continue
        if esc in {"u", "U", "x"}:
            width = {"u": 4, "U": 8, "x": 2}[esc]
            chunk = content[i + 2 : i + 2 + width]
            if len(chunk) == width and all(ch in "0123456789abcdefABCDEF" for ch in chunk):
                try:
                    output.append(chr(int(chunk, 16)))
                    i += 2 + width
                    continue
                except ValueError:
                    pass
        # Keep unknown escapes exactly as they were instead of silently damaging data.
        output.append("\\" + esc)
        i += 2
    return "".join(output)


def _decode_literal(literal: str) -> str:
    quote = literal[0]
    triple = literal.startswith(quote * 3)
    width = 3 if triple else 1
    return _decode_escape(literal[width:-width])


def _encode_literal(value: str) -> str:
    # JSON's double-quoted string escaping is compatible with ordinary GDScript
    # string literals for the characters we emit here.
    return json.dumps(value, ensure_ascii=False)


def extract_godot_strings(source_text: str) -> list[GodotString]:
    entries: list[GodotString] = []
    for match in _ASSIGNMENT.finditer(source_text):
        start = match.end()
        while start < len(source_text) and source_text[start] in " \t":
            start += 1
        end = _scan_string_literal(source_text, start)
        if end is None:
            continue
        literal = source_text[start:end]
        entries.append(
            GodotString(
                index=len(entries) + 1,
                name=match.group("name"),
                value=_decode_literal(literal),
                literal_start=start,
                literal_end=end,
            )
        )
    return entries


def export_editable_text(source_path: Path, output_path: Path, overwrite: bool = False) -> int:
    source_path = source_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if source_path.suffix.lower() != ".gd":
        raise ValueError("Godot text export expects a .gd source file.")
    if output_path == source_path:
        raise ValueError("The editable text output cannot overwrite the original .gd file.")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}")

    source_text, _ = _read_utf8_preserve(source_path)
    entries = extract_godot_strings(source_text)
    if not entries:
        raise ValueError("No string assignments like 'var name = \"text\"' were found in the .gd file.")

    lines = [
        "# Magic Sorter X - Godot editable text v1",
        f"# Source: {source_path.name}",
        "# Edit only lines beginning with |. Keep @@MSX marker lines unchanged.",
        "# A literal | at the start of your text is safe: the first | is only a file marker.",
        "",
    ]
    for entry in entries:
        lines.append(f"@@MSX:BEGIN {entry.index:04d} {entry.name}")
        for line in entry.value.split("\n"):
            lines.append("|" + line)
        lines.append(f"@@MSX:END {entry.index:04d}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return len(entries)


def parse_editable_text(text: str) -> list[tuple[int, str, str]]:
    lines = text.splitlines()
    blocks: list[tuple[int, str, str]] = []
    i = 0
    seen: set[int] = set()
    while i < len(lines):
        begin = _BEGIN.match(lines[i])
        if not begin:
            i += 1
            continue
        index = int(begin.group("index"))
        name = begin.group("name")
        if index in seen:
            raise ValueError(f"Duplicate editable block index: {index}")
        seen.add(index)
        i += 1
        content: list[str] = []
        while i < len(lines):
            end = _END.match(lines[i])
            if end:
                if int(end.group("index")) != index:
                    raise ValueError(f"Mismatched end marker for block {index} ({name}).")
                break
            if not lines[i].startswith("|"):
                raise ValueError(
                    f"Text line inside block {index} ({name}) must begin with '|'. "
                    "This protects marker lines from being confused with dialogue."
                )
            content.append(lines[i][1:])
            i += 1
        else:
            raise ValueError(f"Missing end marker for block {index} ({name}).")
        blocks.append((index, name, "\n".join(content)))
        i += 1
    if not blocks:
        raise ValueError("No @@MSX editable text blocks were found.")
    return blocks


def merge_editable_text(source_text: str, edited_text: str) -> MergeResult:
    entries = extract_godot_strings(source_text)
    if not entries:
        raise ValueError("No editable string assignments were found in the source .gd file.")
    blocks = parse_editable_text(edited_text)

    by_index = {entry.index: entry for entry in entries}
    by_name: dict[str, list[GodotString]] = {}
    for entry in entries:
        by_name.setdefault(entry.name, []).append(entry)

    replacements: list[tuple[int, int, str]] = []
    matched = 0
    changed = 0
    used_spans: set[tuple[int, int]] = set()
    for index, name, value in blocks:
        entry = by_index.get(index)
        if entry is None or entry.name != name:
            candidates = by_name.get(name, [])
            if len(candidates) != 1:
                raise ValueError(
                    f"Cannot uniquely match block {index} ({name}) to the source .gd file."
                )
            entry = candidates[0]
        span = (entry.literal_start, entry.literal_end)
        if span in used_spans:
            raise ValueError(f"The same source string was matched more than once: {name}")
        used_spans.add(span)
        matched += 1
        if value != entry.value:
            changed += 1
            replacements.append((entry.literal_start, entry.literal_end, _encode_literal(value)))

    output = source_text
    for start, end, replacement in sorted(replacements, reverse=True):
        output = output[:start] + replacement + output[end:]
    return MergeResult(len(blocks), matched, changed, output)


def import_edited_text(
    source_path: Path,
    edited_path: Path,
    output_path: Path,
    overwrite: bool = False,
) -> MergeResult:
    source_path = source_path.expanduser().resolve()
    edited_path = edited_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if source_path.suffix.lower() != ".gd":
        raise ValueError("Godot text import expects the original .gd source file.")
    if output_path == source_path:
        raise ValueError("For safety, write to a new .gd file instead of overwriting the original.")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}")

    source_text, source_bom = _read_utf8_preserve(source_path)
    edited_text, _ = _read_utf8_preserve(edited_path)
    result = merge_editable_text(source_text, edited_text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_utf8_preserve(output_path, result.output_text, source_bom)
    return result


def find_gdre_tools(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    if os.getenv("GDRE_TOOLS"):
        candidates.append(Path(os.environ["GDRE_TOOLS"]).expanduser())

    project_root = Path(__file__).resolve().parents[2]
    for name in ("gdre_tools.exe", "gdre_tools"):
        candidates.extend([project_root / name, project_root / "tools" / name])
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError(
        "GDRE Tools was not found. Put gdre_tools.exe next to msx.py (or in a tools folder), "
        "add it to PATH, set GDRE_TOOLS, or pass --gdre PATH."
    )


def _run_gdre(args: list[str], gdre: str | None = None) -> int:
    executable = find_gdre_tools(gdre)
    completed = subprocess.run([str(executable), "--headless", *args], check=False)
    return int(completed.returncode)


def recover_godot_scripts(
    game_path: Path,
    output_dir: Path,
    gdre: str | None = None,
    include: str | None = None,
) -> int:
    game_path = game_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not game_path.is_file():
        raise FileNotFoundError(f"Game package was not found: {game_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    args = [
        f"--recover={game_path}",
        f"--output={output_dir}",
        "--scripts-only",
    ]
    if include:
        args.append(f"--include={include}")
    return _run_gdre(args, gdre)


def list_godot_pack_files(game_path: Path, gdre: str | None = None) -> int:
    game_path = game_path.expanduser().resolve()
    if not game_path.is_file():
        raise FileNotFoundError(f"Game package was not found: {game_path}")
    return _run_gdre([f"--list-files={game_path}"], gdre)


def _compile_gd_to_gdc(source: Path, bytecode: str, gdre: str | None) -> Path:
    with tempfile.TemporaryDirectory(prefix="msx_godot_compile_") as temp:
        temp_path = Path(temp)
        code = _run_gdre(
            [
                f"--compile={source}",
                f"--bytecode={bytecode}",
                f"--output={temp_path}",
            ],
            gdre,
        )
        if code != 0:
            raise RuntimeError(f"GDRE Tools could not compile {source.name} (status {code}).")
        expected = temp_path / f"{source.stem}.gdc"
        candidates = [expected, *temp_path.rglob("*.gdc")]
        compiled = next((path for path in candidates if path.is_file()), None)
        if compiled is None:
            raise RuntimeError("GDRE Tools reported success, but no compiled .gdc file was produced.")
        # The temp directory disappears when this function returns, so keep bytes in a stable temp file.
        fd, stable_name = tempfile.mkstemp(prefix="msx_compiled_", suffix=".gdc")
        os.close(fd)
        stable = Path(stable_name)
        stable.write_bytes(compiled.read_bytes())
        return stable


def patch_godot_pack(
    game_path: Path,
    source_file: Path,
    destination: str,
    output_path: Path,
    gdre: str | None = None,
    bytecode: str | None = None,
) -> int:
    game_path = game_path.expanduser().resolve()
    source_file = source_file.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if not game_path.is_file():
        raise FileNotFoundError(f"Game package was not found: {game_path}")
    if not source_file.is_file():
        raise FileNotFoundError(f"Patch source file was not found: {source_file}")
    if output_path == game_path:
        raise ValueError("For safety, the patched game/package output must be a new file.")
    if output_path.exists():
        raise FileExistsError(f"Patched output already exists: {output_path}")
    if not destination.startswith("res://"):
        raise ValueError("Destination must be the exact Godot resource path, for example res://scripts/questtext.gd")

    patch_source = source_file
    cleanup: Path | None = None
    try:
        if destination.lower().endswith(".gdc") and source_file.suffix.lower() == ".gd":
            if not bytecode:
                raise ValueError(
                    "The package destination is compiled .gdc, but the edited file is .gd. "
                    "Provide --bytecode with the Godot/bytecode version reported by GDRE recovery."
                )
            patch_source = _compile_gd_to_gdc(source_file, bytecode, gdre)
            cleanup = patch_source
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return _run_gdre(
            [
                f"--pck-patch={game_path}",
                f"--output={output_path}",
                f"--patch-file={patch_source}={destination}",
            ],
            gdre,
        )
    finally:
        if cleanup is not None:
            cleanup.unlink(missing_ok=True)
