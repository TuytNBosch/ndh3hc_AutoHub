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

    def execute_script(self, script):
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
    assert lines[0]["url"].endswith("/ShowJob/1") and lines[0]["saved"] == {"html": True, "screenshot": True, "elements": True}
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
