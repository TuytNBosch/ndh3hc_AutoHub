"""AutoHub entry point."""
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from autohub.bootstrap import build_modules
from autohub.config import LOGO_PATH
from autohub.core.logger import setup_logging
from autohub.ui.button_cursor import install_button_cursor
from autohub.ui.main_window import MainWindow
from autohub.ui.theme import apply_dark_theme, enable_dark_titlebar


def main() -> int:
    setup_logging()

    app = QApplication(sys.argv)
    if LOGO_PATH.exists():
        app.setWindowIcon(QIcon(str(LOGO_PATH)))
    apply_dark_theme(app)
    install_button_cursor(app)
    window = MainWindow(build_modules())
    enable_dark_titlebar(window)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
