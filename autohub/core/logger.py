"""Centralized logging setup for the app."""
import logging

from autohub.config import LOG_DIR


LOGGING_ENABLED_KEY = "logging_enabled"


def logging_enabled(settings: dict) -> bool:
    return bool(settings.get(LOGGING_ENABLED_KEY, True))


def set_logging_enabled(enabled: bool) -> None:
    """Switch every log record (file and console) on or off at runtime."""
    logging.disable(logging.NOTSET if enabled else logging.CRITICAL)


def setup_logging(level: int = logging.INFO) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "autohub.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
