"""Turns a Master Sheet request row into the variant dict the WebFlow automation expects (pure)."""
from __future__ import annotations

from typing import Any, Mapping

from autohub.core.normalizers import clean_text, parse_event
from autohub.core.webflow_defaults import WEBFLOW_DEFAULTS, WebFlowDefaults

#: Sheet columns a request row is read from to build a WebFlow variant.
WEBFLOW_SOURCE_COLUMNS = ("C", "H", "BC", "BD", "BE", "BF", "BH", "CL", "CM", "CN", "CQ")


def webflow_variant_from_row(
    part_number: str, row: Mapping[str, Any], defaults: WebFlowDefaults = WEBFLOW_DEFAULTS
) -> dict:
    hardware = clean_text(row.get("BD"))
    return {
        "part_number": part_number,
        "ecu_generation": defaults.ecu_generation,
        "ecu_type": hardware,
        "event": parse_event(row.get("H")),
        "created_at": row.get("C"),
        "general": defaults.general(),
        "ecu": {
            "indi_spec": clean_text(row.get("BC")) or defaults.indi_spec(hardware),
            "family_name": hardware,
            "project_version": clean_text(row.get("BE")),
            "program_version": clean_text(row.get("BF")),
            "tp_level": defaults.tp_level,
        },
        "customer": {
            "ecu_default_id": clean_text(row.get("BH")),
            "ecu_program_id": clean_text(row.get("CL")),
            "ecu_rewriting_id": clean_text(row.get("CM")),
            "security_coefficient": clean_text(row.get("CN")),
            "sw_version": clean_text(row.get("CQ")),
            "component_id": defaults.component_id,
        },
    }
