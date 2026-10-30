"""Shared WebFlow widgets and the job-fill step plan, exercised with fake Selenium elements."""
import pytest

from autohub.services.WebFlow import Constants, components
from autohub.services.WebFlow.Body.Information.Information import Information
from autohub.services.WebFlow.Body.Tab import ECUTab as ecu_tab_module
from autohub.services.WebFlow.Body.Tab.ECUTab import ECUTab
from autohub.services.WebFlow.components import Section, TabLink, select_dropdown
from autohub.services.WebFlow.job_filler import JobFiller


class Element:
    def __init__(self, attrs=None, children=None, displayed=True, selected=False):
        self.attrs = attrs or {}
        self.children = children or {}
        self.displayed, self.selected = displayed, selected
        self.clicks, self.typed, self.cleared = 0, [], 0

    def get_attribute(self, name):
        return self.attrs.get(name)

    def find_element(self, by, value):
        if value not in self.children:
            raise LookupError(value)
        return self.children[value]

    def is_displayed(self):
        return self.displayed

    def is_selected(self):
        return self.selected

    def click(self):
        self.clicks += 1

    def clear(self):
        self.cleared += 1

    def send_keys(self, text):
        self.typed.append(text)


class Driver:
    def __init__(self):
        self.scripts = []

    def execute_script(self, script, element):
        self.scripts.append(element)


@pytest.fixture
def page(monkeypatch):
    """Locators resolve to the elements registered in the returned dict; WebFlow is always idle."""
    elements = {}

    def wait_for(driver, by, locator, timeout=None):
        if locator not in elements:
            raise LookupError(locator)
        return elements[locator]

    monkeypatch.setattr(components, "wait_for", wait_for)
    monkeypatch.setattr(ecu_tab_module, "wait_for", wait_for)
    monkeypatch.setattr(components, "wait_until_idle", lambda driver, timeout=None: True)
    monkeypatch.setattr(Constants, "WEBFLOW_TIMEOUT_CSS", 0)
    return elements


def dropdown(page, selected=None):
    children = {f'.//span[text()="{selected}"]': Element()} if selected else {}
    button = Element(children=children)
    page["//title"] = Element(children={"..": Element(children={"div.btn": button})})
    return button


def test_dropdown_already_showing_the_value_is_not_clicked(page):
    button = dropdown(page, selected="MG1")
    assert select_dropdown(Driver(), "//title", "div.btn", "MG1", lambda: pytest.fail("options read")) is True
    assert button.clicks == 0


def test_dropdown_opens_and_clicks_the_option(page):
    button = dropdown(page)
    option = Element()
    assert select_dropdown(Driver(), "//title", "div.btn", "MG1", lambda: {"MG1": option, "MX17": Element()}) is True
    assert button.clicks == 1 and option.clicks == 1


def test_dropdown_without_the_value_clicks_no_option(page):
    button = dropdown(page)
    other = Element()
    assert select_dropdown(Driver(), "//title", "div.btn", "MG1", lambda: {"MX17": other}) is True  # legacy result
    assert button.clicks == 1 and other.clicks == 0


def test_dropdown_missing_title_is_a_failure(page):
    assert select_dropdown(Driver(), "//missing", "div.btn", "MG1", dict) is False


def section(page, style):
    body = Element({"style": style}, displayed=False)
    header = Element(children={"../..": Element(children={"div.body": body})})
    page["//section"] = Element(children={"..": header, "../..": header.children["../.."]})
    return header, body


def test_section_expands_only_when_collapsed(page):
    header, body = section(page, "display: none;")
    driver = Driver()
    sec = Section(driver, "//section", "div.body")
    assert sec.is_collapsed() and not sec.is_expanded()
    assert sec.expand() is True and header.clicks == 1
    assert driver.scripts and set(driver.scripts) == {body}  # the hidden body is scrolled into view while read

    body.attrs["style"] = "display: block;"
    assert sec.expand() is True and header.clicks == 1
    assert sec.collapse() is True and header.clicks == 2


def test_section_state_of_a_missing_section_is_neither(page):
    sec = Section(Driver(), "//missing", "div.body")
    assert sec.is_expanded() is False and sec.is_collapsed() is False
    assert sec.expand() is False


def test_section_fills_an_input(page):
    _, body = section(page, "display: block;")
    field = Element()
    body.children["input.x"] = field
    sec = Section(Driver(), "//section", "div.body")
    assert sec.fill_input("input.x", "ABC") is True
    assert field.cleared == 1 and field.typed == ["ABC"]
    assert sec.fill_input("input.missing", "ABC") is False


def test_tab_link_clicks_only_an_unselected_tab(page):
    tab = Element()
    page["//tab"] = tab
    link = TabLink(Driver(), "//tab")
    assert link.select() is True and tab.clicks == 1
    tab.selected = True
    assert link.is_selected() and link.select() is True and tab.clicks == 1
    assert TabLink(Driver(), "//missing").select() is False


def test_job_information_reports_whether_it_clicked(page, monkeypatch):
    monkeypatch.setattr(Constants, "BODY_INFORMATION_TITLE_XPATH", "//section")
    monkeypatch.setattr(Constants, "BODY_INFORMATION_BODY_CSS", "div.body")
    header, body = section(page, "display: block;")
    info = Information(Driver())
    assert info.collapse_job_information() is True and header.clicks == 1
    body.attrs["style"] = "display: none;"
    assert info.collapse_job_information() is False
    assert info.expand_job_information() is True and header.clicks == 2


@pytest.mark.parametrize(
    ("icon", "check", "clicks"),
    [(None, None, 0), (None, True, 1), (None, False, 2), ("check", True, 0), ("check", False, 1), ("check", None, 2),
     ("uncheck", False, 0), ("uncheck", None, 1), ("uncheck", True, 2)],
)
def test_lctvorb_checkbox_cycles_to_the_requested_value(page, monkeypatch, icon, check, clicks):
    monkeypatch.setattr(Constants, "ECU_PROJECT_LCTVORB_TITLE_XPATH", "//lctvorb")
    icons = {
        "check": {'checkicon[data-pc-section="checkIcon"]': Element()},
        "uncheck": {'timesicon[data-pc-section="uncheckIcon"]': Element()},
    }
    checkbox = Element(children=icons.get(icon, {}))
    page["//lctvorb"] = Element(children={"..": Element(children={Constants.ECU_PROJECT_LCTVORB_CHECKBOX_CSS: checkbox})})
    tab = ECUTab(Driver())
    tab.expand_ecu_specific_parameters = lambda: True
    assert tab.select_project_lctvorb(check) is True
    assert checkbox.clicks == clicks


class Recorder:
    """Any page method: records its call and returns the configured result."""

    def __init__(self, calls, results):
        self.calls, self.results = calls, results
        self.skipped_fields = []

    def __getattr__(self, name):
        def method(*args):
            self.calls.append((name, *args))
            return self.results.get(name, True)
        return method


def filler(results=None):
    calls = []
    pages = Recorder(calls, results or {})

    class Tabs:
        generaltab = ecutab = customertab = pages

    class Body:
        tab, information, actions = Tabs, pages, pages

    return JobFiller(pages, Body), calls, pages


VARIANT = {
    "part_number": "37820-ABC",
    "general": {"delivery_type": "Plant", "release_class": "C", "release_scope": "S", "limitations": "NO",
                "safety_monitoring": True, "safety_calibration": None, "calibration": False, "data_integration": True},
    "ecu": {"indi_spec": "Spec", "family_name": "", "project_version": "P001", "program_version": None, "tp_level": "3"},
    "customer": {"ecu_default_id": "1", "ecu_program_id": "", "ecu_rewriting_id": "3", "security_coefficient": "",
                 "sw_version": "01", "component_id": "C"},
}


def test_job_filler_plans_the_legacy_steps_in_order():
    job_filler, _, _ = filler()
    names = [step[0] for step in job_filler.steps(VARIANT)]
    assert names == [
        "Close the side menu",
        "Collapse the job information",
        "General: delivery type = Plant",
        "General: release class = C",
        "General: release scope = S",
        "General: limitations = NO",
        "General: safety monitoring SW = True",
        "General: safety calibration response = (none)",
        "General: Bosch calibration data response = False",
        "General: data integration response = True",
        "Select the ECU tab",
        "ECU: indi_spec = Spec",
        "ECU: project_version = P001",
        "ECU: tp_level = 3",
        "Select the Customer tab",
        "Customer: ecu_default_id = 1",
        "Customer: ecu_rewriting_id = 3",
        "Customer: sw_version = 01",
        "Customer: component_id = C",
        "Save the job",
    ]


@pytest.mark.parametrize("part_number", ["37820-6WZ-M610-M6", "37820-6WZ-M710-M6"])
def test_sheet_release_class_reaches_the_webflow_selector(part_number, caplog):
    from autohub.services.MasterSheet.webflow_variants import webflow_variant_from_row

    variant = webflow_variant_from_row(part_number, {"U": "Pre-Production"})
    job_filler, calls, _ = filler()
    with caplog.at_level("INFO", logger="autohub.services.WebFlow"):
        job_filler.fill(variant)
    assert ("select_release_class", "Pre-Production") in calls
    assert ("select_release_class", "Production") not in calls
    assert f"[{part_number}] General: release class = Pre-Production" in caplog.text


def test_job_filler_logs_every_value(caplog):
    job_filler, _, _ = filler()
    with caplog.at_level("INFO", logger="autohub.services.WebFlow"):
        job_filler.fill(VARIANT)
    summary = next(r.getMessage() for r in caplog.records if "Values to fill" in r.getMessage())
    assert "[37820-ABC] Values to fill: General[delivery_type=Plant" in summary
    assert "safety_calibration=(none)" in summary and "family_name=(empty)" in summary
    assert "Customer[ecu_default_id=1" in summary and "component_id=C]" in summary
    assert any("Step: [37820-ABC] General: limitations = NO" == r.getMessage() for r in caplog.records)


def test_job_filler_runs_every_step_and_returns_warnings():
    job_filler, calls, pages = filler()
    pages.skipped_fields.append("stale warning")
    assert job_filler.fill(VARIANT) == []  # warnings are cleared per job
    assert calls[0] == ("select_general_tab",)
    assert ("select_safety_calibration_response", None) in calls
    assert ("select_tp_level", "3") in calls and calls[-1] == ("save",)


def test_job_filler_names_every_failed_step():
    job_filler, calls, _ = filler({"fill_sw_version": False, "save": False})
    with pytest.raises(RuntimeError, match=r"37820-ABC.*Customer: sw_version = 01; \[37820-ABC\] Save the job"):
        job_filler.fill(VARIANT)
    assert calls[-1] == ("save",)  # later steps still ran


def test_job_filler_stops_when_the_general_tab_cannot_be_selected():
    job_filler, calls, _ = filler({"select_general_tab": False})
    with pytest.raises(RuntimeError, match="General tab"):
        job_filler.fill(VARIANT)
    assert calls == [("select_general_tab",)]
