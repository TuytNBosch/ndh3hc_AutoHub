"""HW info file types. Each source turns one file into HW records; HWInfo looks the source up by extension."""
from __future__ import annotations

import email
import io
import logging
import os
import warnings
from email import policy
from typing import Callable, Protocol

import msoffcrypto
import olefile
import openpyxl

from autohub.services.common.sheet_grid import LayoutError, SheetGrid
from autohub.services.HWInfo.parser import is_skipped_sheet, parse_body_table, parse_hw_sheet

_logger = logging.getLogger(__name__)

_MSG_BODY_STREAMS = (("__substg1.0_1000001F", "utf-16-le"), ("__substg1.0_1000001E", "cp1252"))
_MSG_ATTACH_NAME = "__substg1.0_3707001F"
_MSG_ATTACH_DATA = "__substg1.0_37010102"


class HWSource(Protocol):
    def read(self, path: str, password: str) -> list[dict]: ...


def workbook_records(data: bytes, source: str, password: str) -> list[dict]:
    office_file = msoffcrypto.OfficeFile(io.BytesIO(data))
    if office_file.is_encrypted():
        decrypted = io.BytesIO()
        office_file.load_key(password=password)
        office_file.decrypt(decrypted)
        data = decrypted.getvalue()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        workbook = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    records: list[dict] = []
    for sheet in workbook.worksheets:
        if is_skipped_sheet(sheet.title):
            continue
        try:
            records.extend(parse_hw_sheet(SheetGrid.from_openpyxl(sheet), source))
        except LayoutError:
            continue  # a workbook may mix part-number sheets with unrelated ones
    return records


def _email_records(
    name: str, text: str, attachments: list[tuple[str, bytes]], password: str
) -> list[dict]:
    """Attachment workbooks first, then the body table, so the merge prefers the workbook values."""
    records: list[dict] = []
    for attachment_name, data in attachments:
        try:
            records.extend(workbook_records(data, attachment_name, password))
        except Exception as error:
            _logger.warning("Skipping attachment %s of %s: %s", attachment_name, name, error)
    records.extend(parse_body_table(text, f"{name} (email body)"))
    return records


class WorkbookSource:
    def read(self, path: str, password: str) -> list[dict]:
        with open(path, "rb") as f:
            return workbook_records(f.read(), os.path.basename(path), password)


class EmlSource:
    def read(self, path: str, password: str) -> list[dict]:
        with open(path, "rb") as f:
            message = email.message_from_binary_file(f, policy=policy.default)
        body = message.get_body(preferencelist=("plain", "html"))
        attachments = [
            (part.get_filename(), part.get_payload(decode=True))
            for part in message.walk()
            if part.get_filename() and part.get_filename().lower().endswith(".xlsx")
        ]
        return _email_records(os.path.basename(path), body.get_content() if body else "", attachments, password)


class MsgSource:
    def read(self, path: str, password: str) -> list[dict]:
        ole = olefile.OleFileIO(path)
        try:
            text = ""
            for stream, encoding in _MSG_BODY_STREAMS:
                if ole.exists(stream):
                    text = ole.openstream(stream).read().decode(encoding, "replace")
                    break
            attachments = []
            for entry in ole.listdir():
                if entry[0].startswith("__attach_version1.0_") and entry[-1] == _MSG_ATTACH_NAME:
                    name = ole.openstream(entry).read().decode("utf-16-le")
                    data_path = [entry[0], _MSG_ATTACH_DATA]
                    if name.lower().endswith(".xlsx") and ole.exists(data_path):
                        attachments.append((name, ole.openstream(data_path).read()))
        finally:
            ole.close()
        return _email_records(os.path.basename(path), text, attachments, password)


class HWSourceRegistry:
    """Extension -> source. Supporting a new file type is one `register` call."""

    def __init__(self) -> None:
        self._sources: dict[str, HWSource] = {}

    def register(self, extension: str, source: HWSource) -> None:
        self._sources[extension.lower()] = source

    def for_extension(self, extension: str) -> HWSource | None:
        return self._sources.get(extension.lower())

    @property
    def extensions(self) -> list[str]:
        return sorted(self._sources)


def default_registry() -> HWSourceRegistry:
    registry = HWSourceRegistry()
    registry.register(".xlsx", WorkbookSource())
    registry.register(".eml", EmlSource())
    registry.register(".msg", MsgSource())
    return registry
