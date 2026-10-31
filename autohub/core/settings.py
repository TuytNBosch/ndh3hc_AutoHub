"""Persisted user settings (file paths, WebFlow config) under %APPDATA%/AutoHub."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from autohub.config import APP_NAME

APP_DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
_SETTINGS_PATH = APP_DATA_DIR / "settings.json"


class SettingsStore(Protocol):
    """Abstraction UI code depends on, so storage can be swapped (e.g. in-memory for tests)."""

    def load(self) -> dict: ...

    def update(self, **kwargs) -> dict:
        """Merge ``kwargs`` into the persisted settings and save them back."""
        ...


class JsonSettingsStore:
    def __init__(self, path: Path = _SETTINGS_PATH):
        self._path = path

    def load(self) -> dict:
        try:
            with self._path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self, settings: dict) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            tmp_path.replace(self._path)
        except OSError:
            pass

    def update(self, **kwargs) -> dict:
        settings = self.load()
        settings.update(kwargs)
        self.save(settings)
        return settings

