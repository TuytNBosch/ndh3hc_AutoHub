"""Persisted progress of a WebFlow job batch, so it can be retried or resumed after a crash."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

from autohub.core.settings import APP_DATA_DIR

_logger = logging.getLogger(__name__)
_JOURNAL_PATH = APP_DATA_DIR / "webflow_batch.json"


class NonRetryableError(RuntimeError):
    """A failure where another attempt could repeat a server-side effect (e.g. create duplicate jobs)."""


class BatchJournal(Protocol):
    def load(self) -> dict | None: ...

    def save(self, state: dict) -> None: ...

    def clear(self) -> None: ...


class JsonBatchJournal:
    def __init__(self, path: Path = _JOURNAL_PATH):
        self._path = path

    def load(self) -> dict | None:
        try:
            with self._path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError):
            _logger.exception("Could not read the WebFlow batch journal %s", self._path)
            return None
        return data if isinstance(data, dict) else None

    def save(self, state: dict) -> None:
        # In-memory state still protects retries in this session if the disk write fails.
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False, default=str)
            tmp_path.replace(self._path)
        except OSError:
            _logger.exception("Could not save the WebFlow batch journal %s", self._path)

    def clear(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass
