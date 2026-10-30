"""Reads the open PrimeNG drop-down list of a WebFlow form in one query."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import Constants

_logger = logging.getLogger(__name__)


@contextmanager
def fast_lookup(driver: Any):
    """Looks elements up without the implicit wait, so "is it there?" checks don't each cost a second."""
    driver.implicitly_wait(0)
    try:
        yield
    finally:
        driver.implicitly_wait(Constants.IMPLICIT_WAIT)


def read_options(driver: Any, wrapper_class: str, max_items: int) -> dict | None:
    """Option text -> element of the open list, or None when there is none.

    Every ``li[aria-label]`` of the list is read at once; only when the list uses another markup
    are the items probed one by one by id (``<list id without 'list'><n>``)."""
    try:
        wrapper = WebDriverWait(driver, Constants.BODY_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, wrapper_class))
        )
        with fast_lookup(driver):
            list_element = wrapper.find_element(By.TAG_NAME, "ul")
            options = {item.get_attribute("aria-label"): item for item in list_element.find_elements(By.CSS_SELECTOR, "li[aria-label]")}
        if options:
            return options
        return _probe_by_id(driver, list_element.get_attribute("id").replace("list", ""), max_items)
    except Exception:
        _logger.debug("Could not read the drop-down options", exc_info=True)
        return None


def _probe_by_id(driver: Any, item_id: str, max_items: int) -> dict | None:
    options = {}
    with fast_lookup(driver):
        for number in range(max_items):
            try:
                item = WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.ID, item_id + str(number))))
            except Exception:
                break
            options[item.get_attribute("aria-label")] = item
    return options or None
