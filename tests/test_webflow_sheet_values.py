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
                                            ("YES", True), ("No", False), ("X", True), ("", False), (None, False)])
def test_checkbox_sheet_values(value, expected):
    assert webflow_variant_from_row("PN", {"X": value})["general"]["safety_monitoring"] is expected


def test_invalid_checkbox_is_not_silently_replaced():
    with pytest.raises(ValueError, match="PN.*column X"):
        webflow_variant_from_row("PN", {"X": "unexpected"})


def test_blank_cells_stay_empty_except_checkboxes_default_to_false():
    variant = webflow_variant_from_row("PN", {})
    assert not variant["ecu_generation"] and not variant["brand"] and not variant["ecu_type"]
    assert all(variant["general"][key] is False for key in (
        "safety_monitoring", "safety_calibration", "calibration", "data_integration",
    ))
    assert all(variant["general"][key] == "" for key in (
        "delivery_type", "release_class", "release_scope", "limitations",
    ))
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


def test_job_results_retain_each_variants_allocated_number():
    session = Mock()
    session.body.job_creation.get_new_jobs_ids.return_value = ["1", "2"]
    variants = [
        webflow_variant_from_row(part_number, {"Q": "MG1", "R": "Honda", "S": "MG1CS022"})
        for part_number in ("PN1", "PN2")
    ]
    numbers = {"PN1": "10SW072930", "PN2": "10SW072931"}

    def fill_job(variant):
        variant["imported_software_part_number"] = numbers[variant["part_number"]]
        return []

    session._fill_job.side_effect = fill_job
    results = WebFlow.create_and_fill_jobs(session, variants, "tool", "routing")
    assert [(item["PartNumber"], item["JobId"], item["SoftwarePartNumber"]) for item in results] == [
        ("PN1", "1", "10SW072930"), ("PN2", "2", "10SW072931"),
    ]


def _hardware(monkeypatch):
    fields = HardwareFields(Mock())
    fields.driver.find_elements.return_value = []
    fields.sections = {panel: Mock() for panel in fields.sections}
    for section in fields.sections.values():
        section.body.return_value = fields.sections["General info"].body.return_value
    form = fields.sections["General info"].body.return_value.find_element.return_value.find_element.return_value
    monkeypatch.setattr(hardware_module, "pause", lambda: None)
    monkeypatch.setattr(hardware_module, "wait_until_idle", lambda driver, timeout=None: True)
    return fields, form


@pytest.mark.parametrize("column,key,label,kind", [field for field in HARDWARE_FIELDS if field[3] == "text"])
def test_hardware_text_fields_are_written_and_verified(monkeypatch, column, key, label, kind):
    fields, form = _hardware(monkeypatch)
    control = form.find_element.return_value
    control.get_attribute.side_effect = lambda name: "sheet value" if name == "value" else None
    assert fields.fill(key, "sheet value") is True
    control.clear.assert_called_once()
    control.send_keys.assert_called_once_with("sheet value")
    locator = fields.sections[hardware_module._FIELD_PANELS[key]].body.return_value.find_element.call_args.args[1]
    assert label in locator
    fields.sections[hardware_module._FIELD_PANELS[key]].expand.assert_called_once()


def test_hardware_read_only_field_fails_explicitly(monkeypatch):
    fields, form = _hardware(monkeypatch)
    form.find_element.return_value.is_enabled.return_value = False
    assert fields.fill("vehicle_model", "62XS") is False
    form.find_element.return_value.send_keys.assert_not_called()


def test_field_expands_only_its_own_panel(monkeypatch):
    fields, form = _hardware(monkeypatch)
    control = form.find_element.return_value
    control.get_attribute.side_effect = lambda name: "0261S10BN8" if name == "value" else None
    assert fields.fill("hardware_part_number", "0261S10BN8") is True
    fields.sections["Bosch logistic info"].expand.assert_called_once()
    for name, section in fields.sections.items():
        if name != "Bosch logistic info":
            section.expand.assert_not_called()


def test_missing_panel_stops_before_typing(monkeypatch):
    fields, form = _hardware(monkeypatch)
    fields.sections["Ident Numbers"].expand.return_value = False
    assert fields.fill("lead_plant", "SaW") is False
    form.find_element.assert_not_called()


def test_hardware_dropdown_passes_the_sheet_value(monkeypatch):
    fields, form = _hardware(monkeypatch)
    select = Mock(return_value=True)
    monkeypatch.setattr(fields, "_select_plant", select)
    assert fields.fill("lead_plant", "Sheet plant") is True
    select.assert_called_once_with(form, "Sheet plant")


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


def test_pool_import_waits_for_number_and_clicks_only_once(monkeypatch, caplog):
    fields, _ = _hardware(monkeypatch)
    fields.fill = Mock(return_value=True)
    button = fields.sections["Ident Numbers"].body.return_value.find_element.return_value
    button.is_displayed.return_value = True
    button.is_enabled.return_value = True
    field = fields.sections["Ident Numbers"].body.return_value.find_element.return_value
    field.get_attribute.side_effect = ["", "0", "10SW137784"]
    with caplog.at_level("INFO", logger=hardware_module.__name__):
        assert fields.import_software_part_number() is True
    button.click.assert_called_once()
    fields.driver.find_element.assert_not_called()
    locator = fields.sections["Ident Numbers"].body.return_value.find_element.call_args_list[0].args[1]
    assert locator.startswith(".//button") and "Import from pool" in locator
    assert "Software part number = 10SW137784" in caplog.text
    assert fields.imported_software_part_number == "10SW137784"
    assert fields.fill.call_args_list == [
        (("software_name", "10SW137784"),),
        (("customer_software_part_number", "10SW137784"),),
    ]


def test_pool_import_timeout_is_failure_without_retry(monkeypatch):
    fields, _ = _hardware(monkeypatch)
    fields.imported_software_part_number = "previous job number"
    monkeypatch.setattr(hardware_module.Constants, "WEBFLOW_TIMEOUT", 0)
    button = fields.sections["Ident Numbers"].body.return_value.find_element.return_value
    button.is_displayed.return_value = True
    button.is_enabled.return_value = True
    field = fields.sections["Ident Numbers"].body.return_value.find_element.return_value
    field.get_attribute.return_value = ""
    assert fields.import_software_part_number() is False
    assert fields.imported_software_part_number == ""
    button.click.assert_called_once()


def test_pool_import_does_not_retry_uncertain_click(monkeypatch):
    fields, _ = _hardware(monkeypatch)
    button = fields.sections["Ident Numbers"].body.return_value.find_element.return_value
    button.is_displayed.return_value = True
    button.is_enabled.return_value = True
    button.click.side_effect = RuntimeError("connection lost")
    assert fields.import_software_part_number() is False
    button.click.assert_called_once()


def test_pool_import_confirms_save_warning_once_then_waits_for_number(monkeypatch):
    fields, _ = _hardware(monkeypatch)
    fields.fill = Mock(return_value=True)
    control = fields.sections["Ident Numbers"].body.return_value.find_element.return_value
    control.is_displayed.return_value = True
    control.is_enabled.return_value = True
    control.get_attribute.return_value = "10SW137784"
    dialog = Mock()
    dialog.text = "Data filled in by you will be saved before import. Do you want to continue?"
    yes = dialog.find_element.return_value
    fields.driver.find_elements.side_effect = [[dialog], [dialog], []]
    assert fields.import_software_part_number() is True
    yes.click.assert_called_once()
    control.click.assert_called_once()
    assert "Yes" in dialog.find_element.call_args.args[1]


def test_pool_import_does_not_confirm_unrelated_dialog(monkeypatch):
    fields, _ = _hardware(monkeypatch)
    fields.fill = Mock(return_value=True)
    control = fields.sections["Ident Numbers"].body.return_value.find_element.return_value
    control.get_attribute.return_value = "10SW137784"
    dialog = Mock()
    dialog.text = "An unrelated confirmation"
    fields.driver.find_elements.return_value = [dialog]
    assert fields.import_software_part_number() is True
    dialog.find_element.assert_not_called()


@pytest.mark.parametrize("failed_key", ["software_name", "customer_software_part_number"])
def test_pool_import_copy_failure_retains_allocated_number(monkeypatch, failed_key):
    fields, _ = _hardware(monkeypatch)
    fields.fill = Mock(side_effect=lambda key, value: key != failed_key)
    control = fields.sections["Ident Numbers"].body.return_value.find_element.return_value
    control.get_attribute.return_value = "10SW072930"
    assert fields.import_software_part_number() is False
    assert fields.imported_software_part_number == "10SW072930"
    control.click.assert_called_once()


def test_software_name_is_written_in_ident_numbers(monkeypatch):
    fields, form = _hardware(monkeypatch)
    control = form.find_element.return_value
    control.get_attribute.side_effect = lambda name: "10SW072930" if name == "value" else None
    assert fields.fill("software_name", "10SW072930") is True
    control.send_keys.assert_called_once_with("10SW072930")
    fields.sections["Ident Numbers"].expand.assert_called_once()


def test_lead_plant_waits_until_requested_option_is_loaded(monkeypatch):
    fields, _ = _hardware(monkeypatch)
    option = Mock()
    option.get_attribute.return_value = "SaW"
    panel = Mock()
    panel.find_elements.return_value = [option]
    fields.driver.find_elements.side_effect = [[], [], [panel]]
    assert fields._loaded_options("SaW") == {"SaW": option}
    assert fields.driver.find_elements.call_count == 3


def test_plant_scrolls_clicks_trigger_and_waits_for_selection(monkeypatch):
    fields, form = _hardware(monkeypatch)
    control = Mock()
    selected = Mock()
    selected.get_attribute.return_value = "SaW"
    form.find_element.side_effect = [control, selected]
    control.find_element.return_value.get_attribute.return_value = "---"
    fields._loaded_options = Mock(return_value={"SaW": Mock()})
    monkeypatch.setattr(hardware_module.EC, "element_to_be_clickable", lambda element: lambda driver: element)
    assert fields._select_plant(form, "SaW") is True
    fields.driver.execute_script.assert_any_call("arguments[0].scrollIntoView({block: 'center'});", control)
    control.find_element.return_value.click.assert_called_once()
    fields._loaded_options.assert_called_once_with("SaW")


@pytest.mark.parametrize("initial", [None, True, False])
def test_classification_sets_one_variant_and_x_checkboxes(monkeypatch, initial):
    fields, _ = _hardware(monkeypatch)
    section = fields.sections["Classification"]
    checkbox = section.body.return_value.find_element.return_value.find_element.return_value
    states = [initial]
    def value(_checkbox):
        return states[0]
    def click():
        states[0] = {None: True, True: False, False: None}[states[0]]
    checkbox.click.side_effect = click
    monkeypatch.setattr(hardware_module, "checkbox_value", value)
    assert fields.prepare_classification() is True
    assert section.fill_input.call_args.args[1] == "1"
    assert states[0] is False


def test_classification_failure_is_reported(monkeypatch):
    fields, _ = _hardware(monkeypatch)
    fields.sections["Classification"].fill_input.return_value = False
    assert fields.prepare_classification() is False


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
