"""Records the page after every automation step (HTML, screenshot, element list) so a run can be analysed offline.

Works with any object that offers ``page_source``, ``current_url``, ``title``, ``save_screenshot`` and
``execute_script`` (a Selenium driver); it never raises into the automation."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from .page_recorder import DRAIN_SCRIPT, INSTALL_SCRIPT

_logger = logging.getLogger(__name__)

#: Collected inside the browser in one call: every control a step might need to find or fix.
_ELEMENTS_SCRIPT = """
const sel = 'input,select,textarea,button,a,label,option,[role],[class*="select"],[class*="dropdown"],[class*="indicator"]';
const path = (el) => {
  const parts = [];
  for (; el && el.nodeType === 1 && parts.length < 6; el = el.parentElement) {
    let p = el.tagName.toLowerCase();
    if (el.id) { parts.unshift(p + '#' + el.id); break; }
    const same = el.parentElement ? [...el.parentElement.children].filter(c => c.tagName === el.tagName) : [];
    if (same.length > 1) p += ':nth-of-type(' + (same.indexOf(el) + 1) + ')';
    parts.unshift(p);
  }
  return parts.join(' > ');
};
return [...document.querySelectorAll(sel)].slice(0, 1500).map(el => {
  const r = el.getBoundingClientRect();
  return {
    tag: el.tagName.toLowerCase(), id: el.id || null, name: el.getAttribute('name'), type: el.getAttribute('type'),
    class: el.getAttribute('class'), role: el.getAttribute('role'), label: el.getAttribute('label'),
    aria_label: el.getAttribute('aria-label'), placeholder: el.getAttribute('placeholder'),
    href: el.getAttribute('href'), value: el.value === undefined ? null : String(el.value).slice(0, 200),
    text: (el.innerText || '').trim().slice(0, 120), displayed: !!(r.width || r.height),
    disabled: !!el.disabled, css: path(el),
  };
});
"""


def slug(text: str, limit: int = 60) -> str:
    """File-name friendly form of a step name."""
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")[:limit] or "step"


class StepTrace:
    def __init__(self, driver: Any, directory: Path):
        self._driver = driver
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._number = 0
        _logger.info("Recording the WebFlow pages of every step in %s", self._directory)

    @property
    def directory(self) -> Path:
        return self._directory

    def on_step_start(self, name: str) -> None:
        """Starts watching the page's changes and requests (again after a reload)."""
        self._install()

    def _install(self) -> None:
        try:
            self._driver.execute_script(INSTALL_SCRIPT)
        except Exception:
            _logger.debug("Could not install the page recorder", exc_info=True)

    def on_step(self, name: str, ok: bool, seconds: float, error: str = "") -> None:
        """Observer called by ``run_step`` once a step ended."""
        try:
            self._record(name, ok, seconds, error)
        except Exception:
            _logger.exception("Could not record the page after step %r", name)

    def _record(self, name: str, ok: bool, seconds: float, error: str) -> None:
        self._number += 1
        outcome = "OK" if ok else ("ERROR" if error else "FAILED")
        base = self._directory / f"{self._number:03d}_{slug(name)}_{outcome}"
        driver = self._driver
        saved = {"html": False, "screenshot": False, "elements": False, "changes": False}
        changes = self._drain_changes()

        for key, suffix, write in (
            ("html", ".html", lambda path: path.write_text(driver.page_source, encoding="utf-8")),
            ("screenshot", ".png", lambda path: driver.save_screenshot(str(path))),
            ("elements", ".json", lambda path: path.write_text(
                json.dumps(driver.execute_script(_ELEMENTS_SCRIPT), indent=1, ensure_ascii=False), encoding="utf-8")),
            ("changes", ".changes.json", lambda path: path.write_text(
                json.dumps({"step": name, **changes}, indent=1, ensure_ascii=False), encoding="utf-8")),
        ):
            try:
                write(Path(str(base) + suffix))
                saved[key] = True
            except Exception as problem:  # one missing artefact must not lose the others
                _logger.warning("Could not save the %s of step %r: %s", key, name, problem)

        entry = {
            "n": self._number, "step": name, "outcome": outcome, "seconds": round(seconds, 2),
            "url": self._safe(lambda: driver.current_url), "title": self._safe(lambda: driver.title),
            "error": error, "files": base.name, "saved": saved,
            "changes": len(changes["events"]), "requests": sum(e.get("type") == "request" for e in changes["events"]),
            "navigated": changes["navigated"],
        }
        with (self._directory / "index.jsonl").open("a", encoding="utf-8") as index:
            index.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _drain_changes(self) -> dict:
        """What changed on the page during the step; ``navigated`` when the page was reloaded (the recorder was lost)."""
        try:
            drained = self._driver.execute_script(DRAIN_SCRIPT)
        except Exception:
            drained = None
        if not isinstance(drained, dict):
            self._install()
            return {"navigated": True, "dropped": 0, "events": []}
        return {"navigated": False, "dropped": drained.get("dropped", 0), "events": drained.get("events", [])}

    @staticmethod
    def _safe(read) -> str:
        try:
            return read()
        except Exception:
            return ""
