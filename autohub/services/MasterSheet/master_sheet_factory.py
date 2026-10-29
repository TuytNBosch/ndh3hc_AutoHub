"""Picks the master sheet implementation that fits the workbook: MG1 "Master sheet" or the Mx17 flat layout."""
from __future__ import annotations

import html
import re
import zipfile

from autohub.services.MasterSheet import mx17_layout
from autohub.services.MasterSheet.MasterSheet import MasterSheet
from autohub.services.MasterSheet.mx17_sheet import Mx17MasterSheet

_SHEET_TAG = re.compile(r'<sheet\b[^>]*?\bname="([^"]*)"')


def workbook_sheet_names(path: str) -> list[str]:
    """Sheet names read straight from the .xlsx package (no Excel); empty when the file is not a plain xlsx."""
    try:
        with zipfile.ZipFile(path) as package:
            xml = package.read("xl/workbook.xml").decode("utf-8", errors="replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return []
    return [html.unescape(name) for name in _SHEET_TAG.findall(xml)]


def open_master_sheet(path: str) -> MasterSheet:
    """The Mx17 layout for the Honda GDI release workbook, the MG1 layout for everything else."""
    if mx17_layout.is_mx17_sheet_names(workbook_sheet_names(path)):
        return Mx17MasterSheet(path)
    return MasterSheet(path)
