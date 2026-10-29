"""Typed shapes of the data the readers produce and the Master Sheet code consumes (no I/O).

Plain TypedDicts, so the readers' existing dicts are valid values and nothing needs converting.
"""
from __future__ import annotations

from typing import Any, Protocol, TypedDict


class EcuGroup(TypedDict, total=False):
    Event: Any
    MP: Any
    EcuHardware: Any
    Immobi: Any
    SecurityKey: Any
    SecurityKeyIdentifier: Any
    PVERName: Any
    Rows: list[int]


class MainRow(TypedDict, total=False):
    NumCompID: Any
    NumProgID: Any
    CALIBID: Any
    NumReWrecuid: Any
    Row: int


class BootRow(TypedDict, total=False):
    SK1: Any
    SK2: Any
    SK3: Any
    NumProgID: Any
    NumReWrecuid: Any
    Row: int


class GeneralInfo(TypedDict, total=False):
    MY: Any
    Project: Any


class EcuInfoData(TypedDict, total=False):
    GeneralInfo: list[GeneralInfo]
    Ecu: list[EcuGroup]
    Container: list[dict]
    Main: list[MainRow]
    Boot: list[BootRow]


class SystemVariant(TypedDict, total=False):
    Column: str
    PartNumber: Any
    Destination: Any
    Market: Any
    Abolished: bool
    Hardware: Any
    SSID: Any
    ECUMARK: Any
    Displacement: Any
    Transmission: Any
    Emission: Any


class SystemMatrixData(TypedDict, total=False):
    GeneralInfo: list[dict]
    FormB: list[dict]
    Setting: list[dict]


class HWRecord(TypedDict, total=False):
    part_number: str
    hw_ident: str
    b_number: str
    eu_mark: str
    ss_id: str


class KickOffInfo(TypedDict, total=False):
    """Project-level facts from a Kick Off Meeting deck, shared by every variant of the project."""

    power_kw: str
    cylinders: str
    ecu_hw_name: str


class DocumentReader(Protocol):
    """Contract shared by the ECU Info Sheet, System Matrix and HW info readers."""

    last_error: str

    def load_data(self) -> bool:
        """True when the document was read; otherwise False with ``last_error`` explaining why."""
        ...


class HWLookup(Protocol):
    def find(self, part_number: Any) -> HWRecord | None: ...
