from __future__ import annotations

import shutil
from pathlib import Path

from .emojify import emoji_for, emojified_name
from .models import RenamePlan


CATEGORY_BY_EXTENSION = {
    "data": {".json", ".jsonl", ".ndjson", ".xml", ".yaml", ".yml", ".toml", ".csv", ".tsv", ".sql"},
    "documents": {".txt", ".md", ".pdf", ".doc", ".docx", ".odt"},
    "code": {".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp", ".html", ".css"},
    "images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"},
    "audio": {".mp3", ".wav", ".flac", ".m4a", ".ogg"},
    "video": {".mp4", ".mov", ".mkv", ".webm", ".avi"},
    "archives": {".zip", ".7z", ".rar", ".tar", ".gz"},
}
CATEGORY_EMOJI = {
    "data": "🧩", "documents": "📚", "code": "💻", "images": "🖼️",
    "audio": "🎵", "video": "🎬", "archives": "📦", "other": "🗂️",
}


def category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, suffixes in CATEGORY_BY_EXTENSION.items():
        if suffix in suffixes:
            return category
    return "other"


def plan_organize(directory: Path, emoji_names: bool = True) -> list[RenamePlan]:
    plans: list[RenamePlan] = []
    for source in sorted(item for item in directory.iterdir() if item.is_file()):
        category = category_for(source)
        folder = directory / f"{CATEGORY_EMOJI[category]} {category.title()}"
        name = emojified_name(source) if emoji_names else source.name
        destination = folder / name
        plans.append(RenamePlan(source, destination, f"{emoji_for(source)} → {category}"))
    return plans


def apply_organize(plans: list[RenamePlan], copy: bool = False) -> list[RenamePlan]:
    completed: list[RenamePlan] = []
    for plan in plans:
        plan.destination.parent.mkdir(parents=True, exist_ok=True)
        if plan.destination.exists():
            raise FileExistsError(f"Destination already exists: {plan.destination}")
        if copy:
            shutil.copy2(plan.source, plan.destination)
        else:
            shutil.move(str(plan.source), str(plan.destination))
        completed.append(plan)
    return completed
