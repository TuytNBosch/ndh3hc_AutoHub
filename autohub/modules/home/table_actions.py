"""Context menu and keyboard shortcuts (copy / paste / delete / find / replace) for the variant table."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QMenu, QTableWidget, QWidget

from autohub.modules.home.table_clipboard import TableClipboard


class TableActions:
    def __init__(
        self,
        table: QTableWidget,
        clipboard: TableClipboard,
        show_find: Callable[[bool], None],
        extra_menu_views: tuple[QWidget, ...] = (),
    ):
        """`show_find(replace)` opens the find/replace dialog; `extra_menu_views` also get the context menu."""
        self._table = table
        self._clipboard = clipboard
        self._copy = self._make("Copy", QKeySequence.Copy, clipboard.copy_selection)
        self._paste = self._make("Paste", QKeySequence.Paste, clipboard.paste)
        self._delete = self._make("Delete", QKeySequence.Delete, clipboard.delete_selection)
        self._find = self._make("Find...", QKeySequence.Find, lambda: show_find(False))
        self._replace = self._make("Replace...", QKeySequence.Replace, lambda: show_find(True))

        for view in (table, *extra_menu_views):
            view.setContextMenuPolicy(Qt.CustomContextMenu)
            view.customContextMenuRequested.connect(
                lambda pos, v=view: self._show_menu(self._viewport_of(v).mapToGlobal(pos))
            )

    @staticmethod
    def _viewport_of(view: QWidget) -> QWidget:
        return view.viewport() if hasattr(view, "viewport") else view

    def _make(self, text: str, shortcut, handler) -> QAction:
        action = QAction(text, self._table)
        action.setShortcut(shortcut)
        action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        action.triggered.connect(lambda _checked=False: handler())
        self._table.addAction(action)
        return action

    @property
    def _all(self) -> tuple[QAction, ...]:
        return self._copy, self._paste, self._delete, self._find, self._replace

    def _show_menu(self, global_pos: QPoint) -> None:
        cells = self._clipboard.selected_cells()
        has_rows = self._table.rowCount() > 0
        self._copy.setEnabled(bool(cells))
        self._paste.setEnabled(bool(cells) and bool(QApplication.clipboard().text()))
        self._delete.setEnabled(any(self._clipboard.is_editable(r, c) for r, c in cells))
        self._find.setEnabled(has_rows)
        self._replace.setEnabled(has_rows)

        menu = QMenu(self._table)
        for action in (self._copy, self._paste, self._delete):
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction(self._find)
        menu.addAction(self._replace)
        # Disabled actions would also swallow their shortcuts, so restore them on close.
        menu.aboutToHide.connect(lambda: [a.setEnabled(True) for a in self._all])
        menu.exec(global_pos)
