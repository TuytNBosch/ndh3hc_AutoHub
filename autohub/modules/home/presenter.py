"""Home page workflows (New variant / Load / Update / Clear); talks to a view and dialogs, never to widgets."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Protocol

from autohub.core.dialogs import Dialogs
from autohub.core.settings import SettingsStore
from autohub.modules.home.service import VariantService

_logger = logging.getLogger(__name__)

MASTER_SHEET = "Master Sheet"
NEW_VARIANT_TEXT = "New variant"
UPDATE_TEXT = "Update Master Sheet"
LOAD_TEXT = "Load variants"
NEW_VARIANT_TIP = "Create new variant by reading ECU Info Sheet CR and System Matrix CR."

# Field label -> settings.json key (matches the legacy OnlineTool app).
SETTINGS_KEYS = {
    "Master Sheet": "master_sheet_path",
    "ECU Info Sheet": "ecu_info_path",
    "System Matrix": "system_matrix_path",
    "HW Info": "hw_info_path",
    "Kick Off": "kick_off_path",
}
_EXCEL_FILTER = "Excel Files (*.xlsx)"
_HW_INFO_FILTER = "HW info (*.xlsx *.eml *.msg);;All files (*.*)"
_KICK_OFF_FILTER = "Kick Off Meeting (*.pptx)"


class HomeView(Protocol):
    """What the presenter needs from the page; implemented by HomeWidget and by test fakes."""

    def show_file_name(self, field_name: str, path: str) -> None: ...

    def show_rows(self, rows: list[dict]) -> None: ...

    def read_rows(self) -> list[dict]: ...

    def row_count(self) -> int: ...

    def clear_rows(self) -> None: ...

    def set_new_variant_state(self, enabled: bool, text: str) -> None: ...

    def set_load_state(self, enabled: bool, text: str) -> None: ...

    def set_update_state(self, enabled: bool, text: str) -> None: ...

    def set_clear_enabled(self, enabled: bool) -> None: ...

    def publish_variants(self, variants: list[dict]) -> None: ...


#: Runs `func` off the UI thread and reports back: start(func, on_ok, on_error).
TaskStarter = Callable[[Callable, Callable, Callable], None]


class HomePresenter:
    def __init__(
        self,
        view: HomeView,
        service: VariantService,
        settings: SettingsStore,
        dialogs: Dialogs,
        start_task: TaskStarter,
    ):
        self._view = view
        self._service = service
        self._settings = settings
        self._dialogs = dialogs
        self._start_task = start_task
        self._paths: dict[str, str] = {}

    # -- File paths ------------------------------------------------------------------

    def restore_saved_paths(self) -> None:
        saved = self._settings.load()
        for field_name, key in SETTINGS_KEYS.items():
            path = saved.get(key, "")
            if path:
                self._set_path(field_name, path)

    def browse_master_sheet(self) -> None:
        self._pick(MASTER_SHEET, "Select file", _EXCEL_FILTER)

    def _set_path(self, field_name: str, path: str) -> None:
        self._paths[field_name] = path
        self._view.show_file_name(field_name, path)

    def _pick(self, field_name: str, title: str, file_filter: str) -> str:
        path = self._dialogs.pick_file(title, file_filter)
        if path:
            self._set_path(field_name, path)
            self._settings.update(**{SETTINGS_KEYS[field_name]: path})
            _logger.info("%s file selected: %s", field_name, path)
        return path

    def _valid_master_sheet(self, title: str) -> str | None:
        path = self._paths.get(MASTER_SHEET, "")
        if not Path(path).is_file():
            self._dialogs.error(title, "Select a valid Master Sheet file.")
            return None
        return path

    # -- Table -----------------------------------------------------------------------

    def _show_rows(self, rows: list[dict]) -> None:
        self._view.show_rows(rows)
        self._view.set_update_state(False, UPDATE_TEXT)
        self._view.set_clear_enabled(self._view.row_count() > 0)

    def on_table_edited(self) -> None:
        self._view.set_update_state(True, UPDATE_TEXT)

    def clear_table(self) -> None:
        self._view.clear_rows()
        self._view.set_update_state(False, UPDATE_TEXT)
        self._view.set_clear_enabled(False)
        _logger.info("Variant table cleared")

    # -- New variant (compute only, nothing written yet) -------------------------------

    def new_variant(self) -> None:
        master_sheet_path = self._valid_master_sheet("AutoHub")
        if master_sheet_path is None:
            return
        ecu_info_path = self._pick("ECU Info Sheet", "Select ECU Info Sheet CR file", _EXCEL_FILTER)
        if not ecu_info_path:
            return
        system_matrix_path = self._pick("System Matrix", "Select System Matrix CR file", _EXCEL_FILTER)
        if not system_matrix_path:
            return
        hw_info_path = self._ask_hw_info()
        if hw_info_path is None:
            return
        kick_off_path = self._ask_kick_off()
        if kick_off_path is None:
            return

        paths = (master_sheet_path, ecu_info_path, system_matrix_path, hw_info_path, kick_off_path)
        _logger.info("New variant clicked (%s)", paths)
        self._view.set_new_variant_state(False, "Creating...")
        self._view.set_update_state(False, UPDATE_TEXT)
        self._start_task(
            lambda: self._service.compute_new_variants(*paths),
            self._finish_new_variant,
            self._fail_new_variant,
        )

    def _ask_hw_info(self) -> str | None:
        """HW info path, "" to continue without it, or None when the user cancels the whole action."""
        answer = self._dialogs.ask_yes_no_cancel(
            NEW_VARIANT_TEXT,
            "Add HW info (Bosch HW / B-number, from an .xlsx, .eml or .msg file)?\n"
            "Choose No to continue without it.",
        )
        if answer is None:
            return None
        if not answer:
            return ""
        return self._pick("HW Info", "Select HW info file", _HW_INFO_FILTER) or None

    def _ask_kick_off(self) -> str | None:
        """Kick Off Meeting path, "" to continue without it, or None when the user cancels the whole action."""
        answer = self._dialogs.ask_yes_no_cancel(
            NEW_VARIANT_TEXT,
            "Add a Kick Off Meeting (.pptx) to fill power, cylinders and ECU HW name?\n"
            "Choose No to continue without it.",
        )
        if answer is None:
            return None
        if not answer:
            return ""
        return self._pick("Kick Off", "Select Kick Off Meeting file", _KICK_OFF_FILTER) or None

    def _finish_new_variant(self, new_variants: list[dict]) -> None:
        self._view.set_new_variant_state(True, NEW_VARIANT_TEXT)
        self._show_rows(new_variants)
        count = len(new_variants)
        self._view.set_update_state(count > 0, UPDATE_TEXT)  # new rows can be written as they are
        _logger.info("Found %d new variant(s) (not yet written)", count)
        if count == 0:
            self._dialogs.info(NEW_VARIANT_TEXT, "No new variants. Existing variants were skipped.")
        else:
            self._dialogs.info(
                NEW_VARIANT_TEXT,
                f"Found {count} new variant{'s' if count != 1 else ''}. Review/edit below, "
                "then click Update to save to the Master Sheet.",
            )

    def _fail_new_variant(self, error: str) -> None:
        self._view.set_new_variant_state(True, NEW_VARIANT_TEXT)
        _logger.error("New variant failed: %s", error)
        self._dialogs.error(NEW_VARIANT_TEXT, error)

    # -- Update Master Sheet (insert new rows / update existing rows) ------------------

    def update_master_sheet(self) -> None:
        if self._view.row_count() == 0:
            return
        master_sheet_path = self._valid_master_sheet("Update variants")
        if master_sheet_path is None:
            return

        variants = self._view.read_rows()
        _logger.info("Update variants clicked (%d variant(s))", len(variants))
        self._view.set_update_state(False, "Updating...")
        self._start_task(
            lambda: self._service.save_variants(master_sheet_path, variants),
            self._finish_update,
            self._fail_update,
        )

    def _finish_update(self, result) -> None:
        saved, rows, available = result
        count = len(saved)
        _logger.info("Updated %d variant(s) in the Master Sheet", count)
        self._show_rows(rows)
        self._dialogs.info("Update variants", f"Updated {count} variant{'s' if count != 1 else ''} in the Master Sheet.")
        self._view.publish_variants(available)

    def _fail_update(self, error: str) -> None:
        self._view.set_update_state(True, UPDATE_TEXT)
        _logger.error("Update variants failed: %s", error)
        self._dialogs.error("Update variants", error)

    # -- Load variants -----------------------------------------------------------------

    def load_variants(self) -> None:
        master_sheet_path = self._valid_master_sheet(LOAD_TEXT)
        if master_sheet_path is None:
            return
        _logger.info("Load variants clicked (master=%s)", master_sheet_path)
        self._view.set_load_state(False, "Loading...")
        self._start_task(
            lambda: self._service.load_variants(master_sheet_path),
            self._finish_load,
            self._fail_load,
        )

    def _finish_load(self, result) -> None:
        rows, available = result
        self._view.set_load_state(True, LOAD_TEXT)
        self._show_rows(rows)
        count = len(rows)
        _logger.info("Loaded %d variant(s)", count)
        self._dialogs.info(LOAD_TEXT, f"Loaded {count} variant{'s' if count != 1 else ''} from the Master Sheet.")
        self._view.publish_variants(available)

    def _fail_load(self, error: str) -> None:
        self._view.set_load_state(True, LOAD_TEXT)
        _logger.error("Load variants failed: %s", error)
        self._dialogs.error(LOAD_TEXT, error)
