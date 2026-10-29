"""HW part-number information for Honda part numbers, read from whichever source type the file is."""
import logging
import os

from autohub.core.records import HWRecord
from autohub.services.HWInfo.parser import merge_records, normalize_part_number
from autohub.services.HWInfo.sources import HWSourceRegistry, default_registry

_logger = logging.getLogger(__name__)


class HWInfo:
    """Workbook data wins over email-body tables (the source order is decided by each source)."""

    def __init__(self, file_path: str, password: str = "hondabosch", registry: HWSourceRegistry | None = None):
        self.file_path = file_path
        self.password = password
        self.last_error = ""
        self.records: list[dict] = []
        self._registry = registry or default_registry()

    def load_data(self) -> bool:
        name = os.path.basename(self.file_path)
        extension = os.path.splitext(name)[1].lower()
        source = self._registry.for_extension(extension)
        if source is None:
            self.last_error = f"Unsupported HW info file type '{extension}' ({name}). Use {', '.join(self._registry.extensions)}."
            return False
        try:
            records = source.read(self.file_path, self.password)
        except Exception as error:
            self.last_error = f"Could not read HW info '{name}': {error}"
            _logger.error(self.last_error)
            return False

        self.records = merge_records(records)
        if not self.records:
            self.last_error = f"No Honda part numbers with HW data found in '{name}'."
            return False
        return True

    def by_part_number(self) -> dict[str, dict]:
        return {record["part_number"]: record for record in self.records}

    def find(self, part_number) -> HWRecord | None:
        return self.by_part_number().get(normalize_part_number(part_number))
