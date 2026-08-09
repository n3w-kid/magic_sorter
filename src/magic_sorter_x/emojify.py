from __future__ import annotations

import re
from pathlib import Path

from .models import RenamePlan


EMOJI_BY_EXTENSION = {
    ".json": "🧩", ".jsonl": "🧩", ".ndjson": "🧩", ".xml": "📰", ".svg": "🎨",
    ".yaml": "⚙️", ".yml": "⚙️", ".toml": "⚙️", ".ini": "⚙️", ".cfg": "⚙️",
    ".txt": "📝", ".md": "📖", ".pdf": "📕", ".csv": "📊", ".tsv": "📊",
    ".py": "🐍", ".js": "🟨", ".ts": "🔷", ".go": "🐹", ".rs": "🦀",
    ".html": "🌐", ".css": "🎨", ".sql": "🗄️", ".zip": "📦", ".7z": "📦",
    ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️", ".gif": "🎞️", ".webp": "🖼️",
    ".mp3": "🎵", ".wav": "🎵", ".mp4": "🎬", ".mov": "🎬", ".mkv": "🎬",
}
DEFAULT_EMOJI = "📄"
_EMOJI_PREFIX = re.compile(r"^[^\w\s]{1,4}\s+", re.UNICODE)


def emoji_for(path: Path) -> str:
    return EMOJI_BY_EXTENSION.get(path.suffix.lower(), DEFAULT_EMOJI)


def emojified_name(path: Path) -> str:
    if _EMOJI_PREFIX.match(path.name):
        return path.name
    return f"{emoji_for(path)} {path.name}"


def plan_emojify(paths: list[Path], recursive: bool = False) -> list[RenamePlan]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            iterator = path.rglob("*") if recursive else path.glob("*")
            files.extend(item for item in iterator if item.is_file())
    plans: list[RenamePlan] = []
    for source in sorted(set(files)):
        destination = source.with_name(emojified_name(source))
        if destination != source:
            plans.append(RenamePlan(source, destination, f"{emoji_for(source)} {source.suffix or 'file'}"))
    return plans


def apply_plans(plans: list[RenamePlan]) -> list[RenamePlan]:
    completed: list[RenamePlan] = []
    for plan in plans:
        if plan.destination.exists():
            raise FileExistsError(f"Destination already exists: {plan.destination}")
        plan.source.rename(plan.destination)
        completed.append(plan)
    return completed
