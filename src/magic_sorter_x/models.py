from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Document:
    source: Path | None
    kind: str
    data: Any
    raw: str


@dataclass(slots=True, frozen=True)
class RenamePlan:
    source: Path
    destination: Path
    reason: str
