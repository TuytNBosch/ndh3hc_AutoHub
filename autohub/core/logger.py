"""Centralized logging setup for the app."""
import logging

from autohub.config import LOG_DIR


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
