from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from autohub.core.webflow_fields import HARDWARE_FIELDS
from autohub.modules.creation import service as creation_service
from autohub.modules.creation.service import WebFlowConfig, WebFlowJobService
from autohub.services.MasterSheet.webflow_variants import WEBFLOW_SOURCE_COLUMNS, webflow_variant_from_row
from autohub.services.WebFlow.Body.Tab import HardwareFields as hardware_module
from autohub.services.WebFlow.Body.Tab.HardwareFields import HardwareFields
from autohub.services.WebFlow.WebFlow import WebFlow
from tests.fakes import FakeWebFlow


@pytest.mark.parametrize("column,key,label,kind", HARDWARE_FIELDS)
def test_every_hardware_field_reads_its_sheet_column(column, key, label, kind):
    assert column in WEBFLOW_SOURCE_COLUMNS
    variant = webflow_variant_from_row("PN", {column: "sheet value"})
    assert variant["hardware"][key] == "sheet value"


@pytest.mark.parametrize("value,expected", [(True, True), (False, False), (1.0, True), (0.0, False),
                                            ("YES", True), ("No", False), ("X", True), ("", None), (None, None)])
def test_checkbox_sheet_values(value, expected):
    assert webflow_variant_from_row("PN", {"X": value})["general"]["safety_monitoring"] is expected


def test_invalid_checkbox_is_not_silently_replaced():
    with pytest.raises(ValueError, match="PN.*column X"):
        webflow_variant_from_row("PN", {"X": "unexpected"})


def test_blank_cells_never_become_hard_coded_values():
    variant = webflow_variant_from_row("PN", {})
    assert not variant["ecu_generation"] and not variant["brand"] and not variant["ecu_type"]
    assert all(value in ("", None) for value in variant["general"].values())
    assert all(value == "" for value in variant["ecu"].values())
    assert all(value == "" for value in variant["customer"].values())


@pytest.mark.parametrize("missing", ["ecu_generation", "brand", "ecu_type"])
def test_required_creation_fields_are_rejected_before_submission(missing):
    session = Mock()
    variant = {"part_number": "PN", "ecu_generation": "MG1", "brand": "Honda", "ecu_type": "MG1CS022"}
    variant[missing] = ""
    with pytest.raises(ValueError, match=f"PN.*{missing}"):
        WebFlow.create_and_fill_jobs(session, [variant], "tool", "routing")
    session.open_dashboard_page.assert_not_called()


def test_mixed_creation_values_are_rejected():
    session = Mock()
    variant = {"part_number": "PN", "ecu_generation": "MG1", "brand": "Honda", "ecu_type": "MG1CS022"}
    with pytest.raises(ValueError, match="same Master Sheet"):
        WebFlow.create_and_fill_jobs(session, [variant, {**variant, "brand": "Other brand"}], "tool", "routing")


def test_brand_and_ecu_type_are_taken_from_sheet_not_method_defaults():
    session = Mock()
    session.body.job_creation.jobs_creation.return_value = True
    session.body.job_creation.get_new_jobs_ids.return_value = ["1"]
    session._fill_job.return_value = []
    variant = webflow_variant_from_row("PN", {"Q": "MED17", "R": "Sheet brand", "S": "MED17.9"})
    WebFlow.create_and_fill_jobs(session, [variant], "tool", "routing")
    args = session.body.job_creation.jobs_creation.call_args.kwargs
    assert args["ecu_generation"] == "MED17" and args["ecu_type"] == "MED17.9"
    assert args["brand"] == "Sheet brand"


def _hardware(monkeypatch):
    fields = HardwareFields(Mock())
    fields.section = Mock()
    form = fields.section.body.return_value.find_element.return_value.find_element.return_value
    monkeypatch.setattr(hardware_module, "pause", lambda: None)
    monkeypatch.setattr(hardware_module, "wait_until_idle", lambda driver: True)
    return fields, form


@pytest.mark.parametrize("column,key,label,kind", [field for field in HARDWARE_FIELDS if field[3] == "text"])
def test_hardware_text_fields_are_written_and_verified(monkeypatch, column, key, label, kind):
    fields, form = _hardware(monkeypatch)
    control = form.find_element.return_value
    control.get_attribute.side_effect = lambda name: "sheet value" if name == "value" else None
    assert fields.fill(key, "sheet value") is True
    control.clear.assert_called_once()
    control.send_keys.assert_called_once_with("sheet value")
    locator = fields.section.body.return_value.find_element.call_args.args[1]
    assert label in locator


def test_hardware_read_only_field_fails_explicitly(monkeypatch):
    fields, form = _hardware(monkeypatch)
    form.find_element.return_value.is_enabled.return_value = False
    assert fields.fill("vehicle_model", "62XS") is False
    form.find_element.return_value.send_keys.assert_not_called()


def test_hardware_dropdown_passes_the_sheet_value(monkeypatch):
    fields, _ = _hardware(monkeypatch)
    select = Mock(return_value=True)
    monkeypatch.setattr(hardware_module, "select_dropdown", select)
    assert fields.fill("lead_plant", "Sheet plant") is True
    assert select.call_args.args[3] == "Sheet plant"


def test_hardware_multiselect_replaces_previous_selection(monkeypatch):
    fields, form = _hardware(monkeypatch)
    first, second = Mock(), Mock()
    for item, name, initial in ((first, "Brazil", False), (second, "Japan", True)):
        state = {"selected": initial}
        item.get_attribute.side_effect = lambda attr, state=state, name=name: name if attr == "aria-label" else str(state["selected"]).lower()
        item.click.side_effect = lambda state=state: state.update(selected=not state["selected"])
    panel = Mock()
    panel.find_elements.return_value = [first, second]
    fields.driver.find_elements.return_value = [panel]
    assert fields._select_multiple(form, "Brazil") is True
    first.click.assert_called_once()
    second.click.assert_called_once()
    assert form.find_element.return_value.find_element.return_value.click.call_count == 2


def test_hardware_multiselect_missing_option_fails(monkeypatch):
    fields, form = _hardware(monkeypatch)
    panel = Mock()
    panel.find_elements.return_value = []
    fields.driver.find_elements.return_value = [panel]
    assert fields._select_multiple(form, "Brazil") is False


@pytest.mark.parametrize("succeed", [True, False])
def test_total_duration_includes_browser_and_link_writing(monkeypatch, caplog, succeed):
    ticks = iter((10.0, 135.5))
    monkeypatch.setattr(creation_service, "time", SimpleNamespace(perf_counter=lambda: next(ticks)))
    service = WebFlowJobService(FakeWebFlow)
    if not succeed:
        service._create = Mock(side_effect=RuntimeError("browser failed"))
    with caplog.at_level("INFO", logger=creation_service.__name__):
        if succeed:
            service.create_jobs([{"part_number": "PN"}], WebFlowConfig("", "", "", ""))
        else:
            with pytest.raises(RuntimeError, match="browser failed"):
                service.create_jobs([{"part_number": "PN"}], WebFlowConfig("", "", "", ""))
    assert service.last_elapsed_seconds == 125.5
    assert "total time 125.5 seconds" in caplog.text
    assert ("completed" if succeed else "failed") in caplog.text
