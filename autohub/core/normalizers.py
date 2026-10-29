"""Pure text normalisers for values copied from the source documents into the Master Sheet."""
from __future__ import annotations

import re


def clean_text(value) -> str:
    return "" if value is None else str(value).strip()


def normalize_part_number(value) -> str:
    return "" if value is None else re.sub(r"\s+", "", str(value))


def normalize_key_text(value) -> str:
    return re.sub(r"\s+", " ", clean_text(value)).casefold()


def normalize_displacement(value) -> str:
    return re.sub(r"(?i)L$", "", clean_text(value))


def normalize_model_year(value) -> str:
    text = clean_text(value)
    match = re.search(r"(\d+)(?:\.0)?\s*MY", text, re.IGNORECASE)
    return f"MY{match.group(1)}" if match else text


def normalize_emission(value) -> str:
    text = re.sub(r"\s*\([^)]*\)\s*$", "", clean_text(value))
    return text.replace("-", " ")


def normalize_list(value) -> str:
    return re.sub(r",?\s*[\r\n]+\s*", "|", clean_text(value))


def normalize_program_version(value) -> str:
    text = clean_text(value)
    match = re.search(r"V\d+", text, re.IGNORECASE)
    return match.group(0).upper() if match else text


def title_status(value) -> str:
    text = clean_text(value)
    return text.title() if text else ""


def customer_hardware_part_number(part_number: str) -> str:
    return re.sub(r"0-M6$", "", part_number)


def development_number(value) -> str:
    """Bosch development number without its "-00" suffix (0261B00DA8-00 -> 0261B00DA8)."""
    return re.sub(r"-00$", "", clean_text(value))


def ascii_hex(value) -> str:
    return "".join(f"{ord(character):02X}" for character in clean_text(value))


def hex_text(value) -> str:
    """A hex value read from a cell as text; drops the ".0" Excel adds to numbers (2025.0 -> 2025)."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return re.sub(r"^([0-9A-Fa-f]+)\.0+$", r"\1", clean_text(value))


def parse_event(project_purpose) -> str:
    """Extract the event name out of '{project} for {event}/{milestone} event'."""
    text = clean_text(project_purpose)
    match = re.search(r"for\s+(.+?)/(.+?)\s+event$", text, re.IGNORECASE)
    return match.group(1).strip() if match else text
