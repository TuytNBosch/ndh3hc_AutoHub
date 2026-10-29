"""Columns whose value is picked from a list in the webFLOW Configurator (no I/O, no Qt)."""
from __future__ import annotations

_YES_NO = ("Yes", "No")

#: Master Sheet column letter -> the options webFLOW offers (from the webFLOW Configurator manual).
VARIANT_CHOICES: dict[str, tuple[str, ...]] = {
    "T": ("Plant Introduction", "Customer EOL Flashing", "Plant + customer EOL"),
    "U": ("D-Muster", "Pilot", "Pre-Production", "Production", "Field Fix", "Customer service", "EWAK", "Test"),
    "V": ("Data", "Program and Data", "Program", "Basis software", "Boot software"),
    "W": ("NO", "YES \u2013 LIMITED", "YES - NO START"),
    "X": _YES_NO,
    "Y": _YES_NO,
    "Z": _YES_NO,
    "AA": _YES_NO,
}
