"""Main application window: sidebar navigation + stacked module pages."""
from __future__ import annotations

import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from autohub.config import APP_NAME, APP_VERSION, LOGO_PATH
from autohub.core.capabilities import Closable, VariantSink, VariantSource
from autohub.core.module_base import AutoHubModule
from autohub.ui.sidebar import Sidebar

_logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, modules: list[AutoHubModule]):
        super().__init__()
        self._base_title = f"{APP_NAME} v{APP_VERSION}"
        self._module_names = [module.display_name for module in modules]
        self.setWindowTitle(self._base_title)
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.setFixedSize(1024, 700)

        self._sidebar = Sidebar(
            [(module.icon_file, module.display_name) for module in modules],
            [index for index, module in enumerate(modules) if module.pinned_bottom],
        )
        self._pages = QStackedWidget()

        widgets = [module.create_widget() for module in modules]
        for widget in widgets:
            self._pages.addWidget(widget)
        self._wire_cross_module_signals(widgets)

        self._sidebar.moduleSelected.connect(self._on_module_selected)
        if modules:
            self._on_module_selected(0)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._sidebar)
        layout.addWidget(self._pages, stretch=1)
        self.setCentralWidget(central)

    @staticmethod
    def _wire_cross_module_signals(widgets: list[QWidget]) -> None:
        # Pages talk through capability protocols, so MainWindow never knows concrete
        # types, e.g. Home's loaded variants feed Creation's checklist.
        sources = [w for w in widgets if isinstance(w, VariantSource)]
        sinks = [w for w in widgets if isinstance(w, VariantSink)]
        for source in sources:
            for sink in sinks:
                source.variantsLoaded.connect(sink.set_variants)

    def closeEvent(self, event) -> None:
        for i in range(self._pages.count()):
            page = self._pages.widget(i)
            if isinstance(page, Closable):
                page.shutdown()
        super().closeEvent(event)

    def _on_module_selected(self, index: int) -> None:
        _logger.info("Module selected: %s", self._module_names[index])
        self._pages.setCurrentIndex(index)
        self.setWindowTitle(f"{APP_NAME} - {self._module_names[index]}")
