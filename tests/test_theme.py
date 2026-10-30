from PySide6.QtWidgets import QApplication

from autohub.modules.settings.ui import SettingsWidget
from autohub.ui.theme import DARK, LIGHT, apply_theme, is_dark, normalize_theme_mode
from tests.fakes import MemorySettings


def test_mode_resolution():
    assert normalize_theme_mode("nonsense") == "dark" and normalize_theme_mode("light") == "light"
    assert is_dark("dark", False) and not is_dark("light", True)
    assert is_dark("system", True) and not is_dark("system", False)


def test_apply_theme_switches_palette():
    app = QApplication.instance() or QApplication([])
    assert apply_theme(app, "light") is False
    assert app.palette().window().color().name() == LIGHT.window
    assert apply_theme(app, "dark") is True
    assert app.palette().window().color().name() == DARK.window
    assert apply_theme(app, "system") in (True, False)


def test_settings_page_saves_and_applies_the_theme():
    app = QApplication.instance() or QApplication([])
    settings = MemorySettings()
    page = SettingsWidget(settings)
    page._theme.setCurrentIndex(page._theme.findData("light"))
    assert settings.load()["theme"] == "light"
    assert app.palette().window().color().name() == LIGHT.window
    apply_theme(app, "dark")
