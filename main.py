"""AutoHub entry point."""
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from autohub.bootstrap import build_modules
from autohub.config import LOGO_PATH
from autohub.core.logger import logging_enabled, set_logging_enabled, setup_logging
from autohub.ui.button_cursor import install_button_cursor
from autohub.ui.combo_popup import install_combo_popup_style
from autohub.ui.main_window import MainWindow
from autohub.core.settings import JsonSettingsStore
from autohub.ui.theme import apply_theme, set_dark_titlebar


def main() -> int:
    setup_logging()

    app = QApplication(sys.argv)
    if LOGO_PATH.exists():
        app.setWindowIcon(QIcon(str(LOGO_PATH)))
    settings = JsonSettingsStore()
    set_logging_enabled(logging_enabled(settings.load()))
    dark = apply_theme(app, settings.load().get("theme"))
    install_button_cursor(app)
    install_combo_popup_style(app)
    window = MainWindow(build_modules(settings))
    set_dark_titlebar(window, dark)
    window.show()
    QTimer.singleShot(0, window.run_startup_tasks)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
