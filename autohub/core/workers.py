"""Generic background worker: runs a callable off the UI thread, reports back via signals."""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QThread, Signal


class FunctionWorker(QThread):
    finished_ok = Signal(object)
    finished_error = Signal(str)

    def __init__(self, func: Callable[[], Any], parent=None):
        super().__init__(parent)
        self._func = func

    def run(self) -> None:
        try:
            result = self._func()
        except Exception as exc:  # surfaced to the caller via signal, not swallowed
            self.finished_error.emit(str(exc))
        else:
            self.finished_ok.emit(result)


class TaskRunner:
    """Owns the in-flight worker so pages don't each re-implement thread bookkeeping."""

    def __init__(self) -> None:
        self._worker: FunctionWorker | None = None

    def start(
        self,
        func: Callable[[], Any],
        on_ok: Callable[[Any], None],
        on_error: Callable[[str], None],
    ) -> None:
        self._worker = FunctionWorker(func)
        self._worker.finished_ok.connect(on_ok)
        self._worker.finished_error.connect(on_error)
        self._worker.start()
