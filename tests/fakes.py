"""Test doubles: they stand in for Excel, Selenium, Qt dialogs and the settings file."""
from __future__ import annotations

from contextlib import contextmanager

from autohub.modules.home.service import VariantService


class MemorySettings:
    def __init__(self, data=None):
        self.data = dict(data or {})

    def load(self) -> dict:
        return dict(self.data)

    def update(self, **kwargs) -> dict:
        self.data.update(kwargs)
        return dict(self.data)


class FakeWebFlow:
    instances: list = []

    def __init__(self, driver_path="", base_url=""):
        self.quit_calls = 0
        FakeWebFlow.instances.append(self)

    def create_and_fill_jobs(self, variants, tool_version, routing):
        return [{"PartNumber": v["part_number"], "JobId": "1"} for v in variants]

    def quit(self):
        self.quit_calls += 1


class FakeDocument:
    """A reader that never touches Excel."""

    def __init__(self, path="", ok=True, error="", **data):
        self.path = path
        self.ok = ok
        self.last_error = error
        self.opened = self.closed = False
        self.__dict__.update(data)

    def open(self):
        self.opened = True

    def close(self):
        self.closed = True

    def load_data(self) -> bool:
        return self.ok


class FakeMasterSheet(FakeDocument):
    def __init__(self, path="", new_rows=None, rows=None, webflow=None, **kwargs):
        super().__init__(path, **kwargs)
        self.new_rows, self.rows, self.webflow = new_rows or [], rows or [], webflow or []
        self.saved = None
        self.compute_args = None

    def compute_new_variants(self, system_info, ecu_info, hw_info=None):
        self.compute_args = (system_info, ecu_info, hw_info)
        return self.new_rows

    def save_variant_rows(self, variants, save=True):
        self.saved = variants
        return [{"PartNumber": v.get("J")} for v in variants]

    def load_variant_rows(self):
        return self.rows

    def load_webflow_variants(self):
        return self.webflow


@contextmanager
def no_session():
    yield


def build_service(master=None, ecu=None, matrix=None, hw=None) -> VariantService:
    return VariantService(
        master_sheet_factory=lambda path: master or FakeMasterSheet(path),
        ecu_info_factory=lambda path: ecu or FakeDocument(path, ecu_info={"Main": []}),
        system_matrix_factory=lambda path: matrix or FakeDocument(path, system_info={"GeneralInfo": []}),
        hw_info_factory=lambda path: hw or FakeDocument(path),
        session_factory=no_session,
    )


class FakeDialogs:
    def __init__(self, files=(), hw_answer=False):
        self.files = list(files)
        self.hw_answer = hw_answer
        self.infos: list = []
        self.errors: list = []
        self.picked: list = []

    def pick_file(self, title, file_filter):
        self.picked.append(title)
        return self.files.pop(0) if self.files else ""

    def info(self, title, text):
        self.infos.append((title, text))

    def error(self, title, text):
        self.errors.append((title, text))

    def ask_yes_no_cancel(self, title, text):
        return self.hw_answer


class FakeView:
    def __init__(self):
        self.rows: list = []
        self.states: dict = {}
        self.file_names: dict = {}
        self.published: list = []

    def show_file_name(self, field_name, path):
        self.file_names[field_name] = path

    def show_rows(self, rows):
        self.rows = list(rows)

    def read_rows(self):
        return list(self.rows)

    def row_count(self):
        return len(self.rows)

    def clear_rows(self):
        self.rows = []

    def set_new_variant_state(self, enabled, text):
        self.states["new"] = (enabled, text)

    def set_load_state(self, enabled, text):
        self.states["load"] = (enabled, text)

    def set_update_state(self, enabled, text):
        self.states["update"] = (enabled, text)

    def set_clear_enabled(self, enabled):
        self.states["clear"] = enabled

    def publish_variants(self, variants):
        self.published.append(variants)


def run_inline(func, on_ok, on_error):
    """Task starter that runs synchronously, so presenter flows are testable without threads."""
    try:
        result = func()
    except Exception as error:
        on_error(str(error))
    else:
        on_ok(result)
