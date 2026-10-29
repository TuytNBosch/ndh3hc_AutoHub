"""Reads a Kick Off Meeting .pptx (optionally password protected) into project facts."""
import io
import logging
import os
from typing import Iterator

import msoffcrypto

from autohub.core.records import KickOffInfo
from autohub.services.KickOff.parser import parse_kick_off

_logger = logging.getLogger(__name__)

#: Tried in order when the deck is encrypted.
DEFAULT_PASSWORDS = ("honda", "hb")


def _decrypt(path: str, passwords: tuple[str, ...]) -> io.BytesIO | None:
    """The decrypted deck, or None when no password opens it (an unencrypted deck is returned as is)."""
    with open(path, "rb") as handle:
        data = handle.read()
    if not msoffcrypto.OfficeFile(io.BytesIO(data)).is_encrypted():
        return io.BytesIO(data)
    for password in passwords:
        office_file = msoffcrypto.OfficeFile(io.BytesIO(data))
        office_file.load_key(password=password)
        decrypted = io.BytesIO()
        try:
            office_file.decrypt(decrypted)
        except msoffcrypto.exceptions.InvalidKeyError:
            continue
        decrypted.seek(0)
        return decrypted
    return None


def _shape_rows(shapes) -> Iterator[list[str]]:
    """Table rows as their cell texts; every text-box line as a one-cell row."""
    for shape in shapes:
        if hasattr(shape, "shapes"):
            yield from _shape_rows(shape.shapes)
        elif getattr(shape, "has_table", False) and shape.has_table:
            for row in shape.table.rows:
                yield [cell.text.replace("\n", " ").strip() for cell in row.cells]
        elif shape.has_text_frame:
            for line in shape.text_frame.text.splitlines():
                if line.strip():
                    yield [line.strip()]


def _table_rows(presentation) -> Iterator[list[str]]:
    for slide in presentation.slides:
        yield from _shape_rows(slide.shapes)


class KickOffMeeting:
    def __init__(self, file_path: str, passwords: tuple[str, ...] = DEFAULT_PASSWORDS):
        self.file_path = file_path
        self.passwords = passwords
        self.last_error = ""
        self.info: KickOffInfo = {}

    def load_data(self) -> bool:
        name = os.path.basename(self.file_path)
        try:
            deck = _decrypt(self.file_path, self.passwords)
            if deck is None:
                self.last_error = f"Could not open Kick Off Meeting '{name}': none of the known passwords works."
                return False
            from pptx import Presentation  # imported lazily so the app starts without python-pptx

            self.info = parse_kick_off(_table_rows(Presentation(deck)))
        except ImportError:
            self.last_error = "python-pptx is not installed. Run: pip install python-pptx"
            return False
        except Exception as error:
            self.last_error = f"Could not read Kick Off Meeting '{name}': {error}"
            _logger.error(self.last_error)
            return False

        if not self.info:
            self.last_error = f"No engine or ECU information found in Kick Off Meeting '{name}'."
            return False
        return True
