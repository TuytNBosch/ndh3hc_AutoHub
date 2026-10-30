"""Runs browser-automation steps and logs each one: start, outcome, duration (pure; no Selenium)."""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, Sequence

#: (description, action, *arguments) - the action returns True on success.
Step = tuple


def run_step(logger: logging.Logger, name: str, action: Callable[..., Any], *args: Any) -> bool:
    logger.info("Step: %s", name)
    started = time.perf_counter()
    try:
        ok = bool(action(*args))
    except Exception:
        logger.exception("Step raised: %s (after %.1fs)", name, time.perf_counter() - started)
        raise
    elapsed = time.perf_counter() - started
    if ok:
        logger.info("Step OK: %s (%.1fs)", name, elapsed)
    else:
        logger.warning("Step FAILED: %s (%.1fs)", name, elapsed)
    return ok


def run_steps(logger: logging.Logger, steps: Sequence[Step]) -> list[str]:
    """Runs every step, even after a failure, and returns the names of the failed ones."""
    return [step[0] for step in steps if not run_step(logger, step[0], step[1], *step[2:])]
