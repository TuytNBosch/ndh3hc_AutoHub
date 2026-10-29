"""Builds Master Sheet request-row values from the parsed source documents (pure, no Excel)."""
from __future__ import annotations

from datetime import datetime

from autohub.core.normalizers import (
    ascii_hex,
    clean_text,
    customer_hardware_part_number,
    hex_text,
    normalize_displacement,
    normalize_emission,
    normalize_key_text,
    normalize_list,
    normalize_model_year,
    normalize_part_number,
    normalize_program_version,
    title_status,
)
from autohub.core.records import BootRow, EcuGroup, EcuInfoData, HWLookup, HWRecord, SystemMatrixData
from autohub.core.webflow_defaults import WEBFLOW_DEFAULTS

_SECURITY_KEY_FIELDS = ("SK1", "SK2", "SK3")
_PROJECT_NUMBER_FIRST_PART = 159


def variant_key(customer_event_purpose, part_number, initial_software_id) -> tuple[str, str, str]:
    return (
        normalize_key_text(customer_event_purpose),
        normalize_part_number(part_number).upper(),
        normalize_part_number(initial_software_id).upper(),
    )


def variant_key_from_values(values: dict) -> tuple[str, str, str]:
    return variant_key(values.get("H"), values.get("J"), values.get("BI"))


def index_system_variants(system_info: SystemMatrixData) -> dict[str, dict]:
    """Part number -> its General, Form B and Setting data merged by System Matrix column."""
    form_b_by_column = {item["Column"]: item for item in system_info.get("FormB", [])}
    setting_by_column = {item["Column"]: item for item in system_info.get("Setting", [])}
    variants: dict[str, dict] = {}

    for general in system_info.get("GeneralInfo", []):
        part_number = normalize_part_number(general.get("PartNumber"))
        if not part_number:
            continue
        if part_number in variants and general.get("Abolished"):
            continue  # a part number listed again after being abolished keeps its live column
        column = general["Column"]
        variants[part_number] = {
            **general,
            **form_b_by_column.get(column, {}),
            **setting_by_column.get(column, {}),
        }
    return variants


def security_type_1_value(boot: BootRow) -> str:
    """SecuAcs_CustTypeI: the Boot row's Security Type Ⅰ SK1, SK2 and SK3 values joined in order."""
    return "".join(hex_text(boot.get(field)) for field in _SECURITY_KEY_FIELDS)


def ecu_for_variant(ecu_info: EcuInfoData, main: dict) -> EcuGroup:
    """The ECU settings group (event / MP) whose rows include this variant's row."""
    groups = ecu_info.get("Ecu") or []
    row = main.get("Row")
    for group in groups:
        if row in group.get("Rows", ()):
            return group
    return groups[0] if groups else {}


def _apply_hw_info(request_values: dict, hw: HWRecord) -> None:
    for column, field in (("AN", "hw_ident"), ("AO", "b_number")):
        if hw.get(field):
            request_values[column] = hw[field]
    # The System Matrix stays authoritative for SS-ID / EU-mark; HW info only fills gaps.
    for column, field in (("CY", "eu_mark"), ("CZ", "ss_id")):
        if not request_values.get(column) and hw.get(field):
            request_values[column] = hw[field]


def build_request_values(
    general: dict,
    ecu: EcuGroup,
    main: dict,
    boot: dict,
    system_variant: dict,
    hw: HWRecord | None = None,
    now: datetime | None = None,
) -> dict:
    """Column-letter -> value for one variant's REQ row (including the created date "C")."""
    defaults = WEBFLOW_DEFAULTS
    project = clean_text(general.get("Project"))
    event = clean_text(ecu.get("Event"))
    milestone = clean_text(ecu.get("MP"))
    part_number = normalize_part_number(main.get("NumCompID"))
    program_id = clean_text(main.get("NumProgID"))
    hardware = clean_text(system_variant.get("Hardware"))
    project_purpose = f"{project} for {event}/{milestone} event" if project and event and milestone else ""

    request_values = {
        "C": now or datetime.now(),
        "H": project_purpose,
        "J": part_number,
        "Q": defaults.ecu_generation,
        "R": "Honda",
        "S": hardware,
        "BI": program_id,
        "CO": clean_text(ecu.get("SecurityKey")),
        "CP": clean_text(ecu.get("SecurityKeyIdentifier")),
        "CS": part_number,
        "CT": clean_text(main.get("NumReWrecuid")),
        "CU": clean_text(main.get("CALIBID")),
        "CV": program_id,
        "CY": clean_text(system_variant.get("ECUMARK")),
        "CZ": clean_text(system_variant.get("SSID")),
        "AL": _PROJECT_NUMBER_FIRST_PART,
        "AB": project,
        "AD": title_status(ecu.get("Immobi")),
        "AE": normalize_displacement(system_variant.get("Displacement")),
        "AF": normalize_model_year(general.get("MY")),
        "AH": normalize_emission(system_variant.get("Emission")),
        "AI": clean_text(system_variant.get("Transmission")),
        "AJ": normalize_list(system_variant.get("Destination")),
        "AQ": part_number,
        "AR": customer_hardware_part_number(part_number),
        "AM": part_number.replace("-", ""),
        "BD": hardware,
        "BE": project,
        "BF": normalize_program_version(ecu.get("PVERName")),
        "BH": defaults.ecu_default_id,
        "CL": ascii_hex(program_id),
        "CM": defaults.ecu_rewriting_id,
        "CQ": defaults.sw_version,
        "AU": "HONDA",
    }
    security_type_1 = security_type_1_value(boot)
    if security_type_1:
        request_values["CN"] = security_type_1
    if hw:
        _apply_hw_info(request_values, hw)
    return request_values


def compute_new_variant_rows(
    ecu_info: EcuInfoData,
    system_info: SystemMatrixData,
    existing_keys: set[tuple[str, str, str]],
    hw: HWLookup | None = None,
    now: datetime | None = None,
) -> list[dict]:
    """REQ-row values for the variants not yet in the sheet (keys in `existing_keys`)."""
    main_variants = ecu_info.get("Main", [])
    container_variants = ecu_info.get("Container", [])
    boot_variants = ecu_info.get("Boot", [])
    if not main_variants:
        raise ValueError("EcuInfoSheet does not contain Main variant data.")
    if len(container_variants) != len(main_variants):
        raise ValueError("EcuInfoSheet Main and Container variant counts do not match.")
    if len(boot_variants) < len(main_variants):
        raise ValueError("EcuInfoSheet does not contain enough Boot variant data.")

    system_variants = index_system_variants(system_info)
    general_items = ecu_info.get("GeneralInfo")
    general = general_items[0] if general_items else {}
    seen = set(existing_keys)
    new_variants: list[dict] = []

    for index, main in enumerate(main_variants):
        part_number = normalize_part_number(main.get("NumCompID"))
        system_variant = system_variants.get(part_number)
        if system_variant is None:
            raise ValueError(f"System Matrix variant not found for {main.get('NumCompID')}")

        values = build_request_values(
            general,
            ecu_for_variant(ecu_info, main),
            main,
            boot_variants[index],
            system_variant,
            hw.find(part_number) if hw else None,
            now,
        )
        key = variant_key_from_values(values)
        if key in seen:
            continue
        seen.add(key)
        values.pop("C", None)  # created date is stamped fresh on write, not editable here
        new_variants.append(values)

    return new_variants
