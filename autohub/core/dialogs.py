"""User-interaction ports (file pick, messages) so workflows run in tests without a visible window."""
from __future__ import annotations

from typing import Mapping, Protocol, Sequence

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from autohub.core.file_fields import FileField
from autohub.core.file_form_dialog import FileFormDialog
from autohub.core.progress import ProgressWindow
from autohub.core.progress_dialog import ProgressDialog


class Dialogs(Protocol):
    def pick_file(self, title: str, file_filter: str) -> str:
        """Selected path, or "" when the user cancels."""
        ...

    def info(self, title: str, text: str) -> None: ...

    def error(self, title: str, text: str) -> None: ...

    def ask_yes_no_cancel(self, title: str, text: str) -> bool | None:
        """True for Yes, False for No, None for Cancel."""
        ...

    def open_progress(self, title: str) -> ProgressWindow: ...

    def ask_files(self, title: str, fields: Sequence[FileField], initial: Mapping[str, str]) -> dict[str, str] | None:
        """Field name -> chosen path ("" for an optional field left empty), or None when cancelled."""
        ...


class QtDialogs:
    def __init__(self, parent: QWidget | None = None):
        self._parent = parent

    def pick_file(self, title: str, file_filter: str) -> str:
        path, _ = QFileDialog.getOpenFileName(self._parent, title, filter=file_filter)
        return path

    def info(self, title: str, text: str) -> None:
        QMessageBox.information(self._parent, title, text)

    def error(self, title: str, text: str) -> None:
        QMessageBox.critical(self._parent, title, text)

    def ask_yes_no_cancel(self, title: str, text: str) -> bool | None:
        answer = QMessageBox.question(
            self._parent, title, text, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.No
        )
        if answer == QMessageBox.Cancel:
            return None
        return answer == QMessageBox.Yes

    def open_progress(self, title: str) -> ProgressWindow:
        return ProgressDialog(title, self._parent)

    def ask_files(self, title: str, fields: Sequence[FileField], initial: Mapping[str, str]) -> dict[str, str] | None:
        dialog = FileFormDialog(title, fields, initial, self._parent)
        return dialog.values() if dialog.exec() == FileFormDialog.Accepted else None
