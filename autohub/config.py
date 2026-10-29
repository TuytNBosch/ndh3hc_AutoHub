"""App-wide constants and paths."""
from pathlib import Path

APP_NAME = "AutoHub"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCES_DIR = BASE_DIR / "autohub" / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
LOGO_PATH = RESOURCES_DIR / "logo.png"
HOME_BANNER_PATH = RESOURCES_DIR / "home_banner.png"
LOG_DIR = BASE_DIR / "logs"
