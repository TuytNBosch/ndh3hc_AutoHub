"""Describes the source files an action needs, so one dialog can ask for all of them at once."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileField:
    name: str  # also the key of the answer
    file_filter: str
    required: bool = True
    hint: str = ""
