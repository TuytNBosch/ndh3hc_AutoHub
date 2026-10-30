import json
import logging

from autohub.services.WebFlow import step_log
from autohub.services.WebFlow.step_trace import StepTrace, slug


class FakeDriver:
    current_url = "https://h/app/ShowJob/1"
    title = "WebFlow"
    page_source = "<html><body>hi</body></html>"

    def save_screenshot(self, path):
        open(path, "wb").write(b"png")

    installs = 0
    reloaded = False

    def execute_script(self, script):
        if "__autohubRec.drain" in script:
            return None if self.reloaded else {"events": [{"type": "added"}, {"type": "request", "url": "u"}], "dropped": 2}
        if "__autohubRec = rec" in script:
            FakeDriver.installs += 1
            return True
        return [{"tag": "input", "id": "a"}]


class BrokenDriver(FakeDriver):
    @property
    def page_source(self):
        raise RuntimeError("browser gone")

    def save_screenshot(self, path):
        raise RuntimeError("browser gone")


def test_slug_is_file_name_safe():
    assert slug("[P1] ECU: indi_spec = A/B") == "P1_ECU_indi_spec_A_B"
    assert slug("???") == "step"


def test_each_step_is_recorded_with_html_screenshot_elements_and_index(tmp_path):
    trace = StepTrace(FakeDriver(), tmp_path / "run")
    trace.on_step("Select brand", True, 0.5)
    trace.on_step("Save", False, 1.0, "raised an exception")
    names = sorted(p.name for p in (tmp_path / "run").iterdir())
    assert "001_Select_brand_OK.html" in names and "001_Select_brand_OK.png" in names
    assert "001_Select_brand_OK.json" in names and "002_Save_ERROR.html" in names
    lines = [json.loads(x) for x in (tmp_path / "run" / "index.jsonl").read_text().splitlines()]
    assert [(e["n"], e["outcome"]) for e in lines] == [(1, "OK"), (2, "ERROR")]
    assert lines[0]["url"].endswith("/ShowJob/1")
    assert lines[0]["saved"] == {"html": True, "screenshot": True, "elements": True, "changes": True}
    assert (lines[0]["changes"], lines[0]["requests"], lines[0]["navigated"]) == (2, 1, False)
    changes = json.loads((tmp_path / "run" / "001_Select_brand_OK.changes.json").read_text())
    assert changes["step"] == "Select brand" and changes["dropped"] == 2 and len(changes["events"]) == 2
    assert json.loads((tmp_path / "run" / "001_Select_brand_OK.json").read_text()) == [{"tag": "input", "id": "a"}]


def test_a_dead_browser_never_breaks_the_run(tmp_path):
    trace = StepTrace(BrokenDriver(), tmp_path)
    trace.on_step("x", True, 0.1)  # must not raise
    entry = json.loads((tmp_path / "index.jsonl").read_text())
    assert entry["saved"]["html"] is False and entry["saved"]["elements"] is True


def test_run_step_reports_to_the_observer_and_it_can_be_removed(tmp_path):
    log = logging.getLogger("t")
    seen = []

    class Obs:
        def on_step(self, name, ok, seconds, error=""):
            seen.append((name, ok, error))

    step_log.set_step_observer(Obs())
    try:
        step_log.run_step(log, "a", lambda: True)
        step_log.run_step(log, "b", lambda: False)
        try:
            step_log.run_step(log, "c", lambda: 1 / 0)
        except ZeroDivisionError:
            pass
    finally:
        step_log.set_step_observer(None)
    step_log.run_step(log, "d", lambda: True)
    assert seen == [("a", True, ""), ("b", False, ""), ("c", False, "raised an exception")]


def test_an_observer_without_on_step_is_rejected_at_once():
    import pytest

    with pytest.raises(TypeError):
        step_log.set_step_observer(lambda *args: None)  # a bare function, as WebFlow once passed
    step_log.set_step_observer(None)


def test_webflow_hands_the_recorder_object_to_the_observer():
    from pathlib import Path

    source = Path(step_log.__file__).with_name("WebFlow.py").read_text(encoding="utf-8")
    assert "set_step_observer(StepTrace(self, Path(trace_dir)))" in source


def test_recorder_is_installed_at_each_step_start_and_a_reload_is_reported(tmp_path):
    driver = FakeDriver()
    FakeDriver.installs = 0
    trace = StepTrace(driver, tmp_path)
    trace.on_step_start("open job")
    assert FakeDriver.installs == 1
    driver.reloaded = True  # the page was reloaded during the step: the recorder is gone
    trace.on_step("open job", True, 1.0)
    entry = json.loads((tmp_path / "index.jsonl").read_text())
    assert entry["navigated"] is True and entry["changes"] == 0
    assert FakeDriver.installs == 2  # put back for the next step


def test_run_step_tells_the_observer_before_the_step_runs():
    order = []

    class Obs:
        def on_step_start(self, name):
            order.append(("start", name))

        def on_step(self, name, ok, seconds, error=""):
            order.append(("end", name))

    step_log.set_step_observer(Obs())
    try:
        step_log.run_step(logging.getLogger("t"), "s", lambda: order.append("run") or True)
    finally:
        step_log.set_step_observer(None)
    assert order == [("start", "s"), "run", ("end", "s")]
