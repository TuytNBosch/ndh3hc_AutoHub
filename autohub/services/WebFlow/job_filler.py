"""Fills one opened WebFlow job from a variant dict: builds the step list and runs it."""
from __future__ import annotations

import logging
from typing import Any
from autohub.core.webflow_fields import HARDWARE_FIELDS

from .step_log import Step, run_step, run_steps

_logger = logging.getLogger(__name__)

# (page method, variant key): filled only when the variant has a value. Add a field with one line.
ECU_FIELDS = (
    ("fill_indi_spec", "indi_spec"),
    ("fill_family_name", "family_name"),
    ("fill_project_version", "project_version"),
    ("fill_program_version", "program_version"),
    ("select_tp_level", "tp_level"),
)
CUSTOMER_FIELDS = (
    ("fill_ecu_default_id", "ecu_default_id"),
    ("fill_ecu_program_id", "ecu_program_id"),
    ("fill_ecu_rewriting_id", "ecu_rewriting_id"),
    ("fill_security_coefficient", "security_coefficient"),
    ("fill_sw_version", "sw_version"),
    ("fill_component_id", "component_id"),
)
# (label, page method, variant key): fill in this order, skipping blank cells.
GENERAL_FIELDS = (
    ("delivery type", "select_delivery_type", "delivery_type"),
    ("release class", "select_release_class", "release_class"),
    ("release scope", "select_release_scope", "release_scope"),
    ("limitations", "select_limitations", "limitations"),
    ("safety monitoring SW", "select_safety_monitoring_sw", "safety_monitoring"),
    ("safety calibration response", "select_safety_calibration_response", "safety_calibration"),
    ("Bosch calibration data response", "select_bosch_cal_data_response", "calibration"),
    ("data integration response", "select_data_integration_response", "data_integration"),
)


class JobFiller:
    """Depends only on the page objects it is given (``side_menu_bar`` and ``body``)."""

    def __init__(self, side_menu_bar: Any, body: Any):
        self.side_menu_bar = side_menu_bar
        self.body = body

    def steps(self, variant: dict) -> list[Step]:
        """The steps that fill the General, ECU and Customer tabs of the open job and save it."""
        general, ecu_tab, customer_tab = self.body.tab.generaltab, self.body.tab.ecutab, self.body.tab.customertab
        steps: list[Step] = [
            ("Close the side menu", self.side_menu_bar.close_menubar),
            ("Collapse the job information", self.body.information.collapse_job_information),
        ]
        steps += [
            (f"General: {label} = {display_value(variant['general'][key])}", getattr(general, method), variant["general"][key])
            for label, method, key in GENERAL_FIELDS
            if variant["general"].get(key) not in (None, "")
        ]
        for _, key, label, _ in HARDWARE_FIELDS:
            if key == "software_part_number":
                continue  # WebFlow allocates this number through Import from pool.
            value = variant.get("hardware", {}).get(key)
            if value:
                steps.append((f"General: {label} = {value}", general.fill_hardware_field, key, value))
                if key == "lead_plant":
                    steps.append(("General: Import software part number from pool", general.import_software_part_number))
        steps.append(("Select the ECU tab", ecu_tab.select_ecu_tab))
        steps += _optional_steps("ECU", ecu_tab, ECU_FIELDS, variant["ecu"])
        steps.append(("Select the Customer tab", customer_tab.select_customer_tab))
        steps += _optional_steps("Customer", customer_tab, CUSTOMER_FIELDS, variant["customer"])
        steps.append(("Save the job", self.body.actions.save))
        return steps

    def fill(self, variant: dict) -> list[str]:
        """Fills and saves the open job; returns the warnings of values WebFlow would not accept.

        Raises RuntimeError naming every failed step."""
        part_number = variant["part_number"]
        general = self.body.tab.generaltab
        general.skipped_fields.clear()
        _logger.info("[%s] Values to fill: %s", part_number, describe_values(variant))
        for field, value in variant.get("unmapped_fields", {}).items():
            warning = f"Master Sheet {field} = {value}: no matching control in the recorded WebFlow form; not filled."
            general.skipped_fields.append(warning)
            _logger.warning("[%s] %s", part_number, warning)
        if not run_step(_logger, f"[{part_number}] Select the General tab", general.select_general_tab):
            raise RuntimeError("Could not select the General tab.")

        failed = run_steps(_logger, [(f"[{part_number}] {step[0]}", *step[1:]) for step in self.steps(variant)])
        if failed:
            raise RuntimeError(f"Could not fill all values for {part_number}. Failed: {'; '.join(failed)}")
        return list(general.skipped_fields)


def display_value(value: Any) -> str:
    """How a value appears in the log: empty text and None (a cleared checkbox) are spelled out."""
    if value is None:
        return "(none)"
    if value == "":
        return "(empty)"
    return str(value)


def describe_values(variant: dict) -> str:
    """Every value of the General, ECU and Customer tabs, e.g. ``General[delivery_type=X, ...]; ECU[...]``."""
    return "; ".join(
        f"{title}[" + ", ".join(f"{key}={display_value(value)}" for key, value in variant.get(section, {}).items()) + "]"
        for title, section in (("General", "general"), ("Hardware/Plant", "hardware"), ("ECU", "ecu"), ("Customer", "customer"))
    )


def _optional_steps(section: str, page: Any, fields: tuple, values: dict) -> list[Step]:
    return [
        (f"{section}: {key} = {values[key]}", getattr(page, method), values[key])
        for method, key in fields
        if values.get(key)
    ]
