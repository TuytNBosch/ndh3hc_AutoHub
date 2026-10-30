from autohub.core.capabilities import Closable, VariantSink, VariantSource
from autohub.core.settings import JsonSettingsStore
from autohub.modules.creation.service import WebFlowConfig, WebFlowJobService
from autohub.modules.creation.ui import CreationWidget
from autohub.modules.home.ui import HomeWidget
from tests.fakes import FakeDialogs, FakeWebFlow, MemorySettings, build_service


def test_json_settings_store_roundtrip(tmp_path):
    store = JsonSettingsStore(tmp_path / "s.json")
    assert store.load() == {}
    store.update(a=1)
    store.update(b=2)
    assert store.load() == {"a": 1, "b": 2}


def test_webflow_service_replaces_and_quits_previous_session():
    FakeWebFlow.instances.clear()
    service = WebFlowJobService(webflow_factory=FakeWebFlow)
    config = WebFlowConfig("", "url", "v", "r")
    variants = [{"part_number": "P1", "ecu_type": "E"}]

    assert service.create_jobs(variants, config) == [{"PartNumber": "P1", "JobId": "1"}]
    service.create_jobs(variants, config)
    first, second = FakeWebFlow.instances
    assert first.quit_calls == 1 and second.quit_calls == 0

    service.shutdown()
    assert second.quit_calls == 1


def test_pages_expose_capabilities(qapp):
    home = HomeWidget(build_service(), MemorySettings(), FakeDialogs())
    creation = CreationWidget(WebFlowJobService(webflow_factory=FakeWebFlow), MemorySettings())
    assert isinstance(home, VariantSource)
    assert isinstance(creation, VariantSink)
    assert isinstance(creation, Closable)


def test_checklist_selection_persists_through_injected_settings(qapp):
    settings = MemorySettings({"selected_variants": ["P2"]})
    creation = CreationWidget(WebFlowJobService(webflow_factory=FakeWebFlow), settings)
    creation.set_variants(
        [
            {"part_number": "P1", "ecu_type": "E", "event": "A"},
            {"part_number": "P2", "ecu_type": "E", "event": "B"},
        ]
    )
    assert [v["part_number"] for v in creation._checklist.selected_variants()] == ["P2"]
    creation._checklist._checkboxes["P1"].setChecked(True)
    assert settings.data["selected_variants"] == ["P1", "P2"]


def test_progress_dialog_can_only_be_closed_after_the_action_finished():
    from PySide6.QtGui import QCloseEvent
    from PySide6.QtWidgets import QApplication

    from autohub.core.progress_dialog import ProgressDialog

    QApplication.instance() or QApplication([])
    dialog = ProgressDialog("Load variants")
    dialog.step("Reading...")
    QApplication.processEvents()
    event = QCloseEvent()
    dialog.closeEvent(event)
    dialog.reject()
    assert not event.isAccepted() and dialog.isVisible()

    dialog.succeed("Loaded 3 variants from the Master Sheet.")
    QApplication.processEvents()
    assert dialog._buttons.isEnabled() and "Loaded 3 variants" in dialog._status.text()
    event = QCloseEvent()
    dialog.closeEvent(event)
    assert event.isAccepted()
    dialog.reject()


def test_file_form_dialog_needs_the_required_files(tmp_path):
    from PySide6.QtWidgets import QApplication, QDialogButtonBox

    from autohub.core.file_fields import FileField
    from autohub.core.file_form_dialog import FileFormDialog

    QApplication.instance() or QApplication([])
    real = tmp_path / "a.xlsx"
    real.write_bytes(b"x")
    dialog = FileFormDialog("New variant", [FileField("ECU", "*"), FileField("HW", "*", required=False)], {})
    ok = dialog._buttons.button(QDialogButtonBox.Ok)
    assert not ok.isEnabled()
    dialog._edits["ECU"].setText(str(real))
    assert ok.isEnabled()
    dialog._edits["HW"].setText(str(tmp_path / "missing.eml"))
    assert not ok.isEnabled() and "not found" in dialog._message.text()
    dialog._edits["HW"].setText("")
    assert ok.isEnabled() and dialog.values() == {"ECU": str(real), "HW": ""}


def test_create_jobs_reports_progress_and_forwards_it():
    seen = []
    service = WebFlowJobService(FakeWebFlow)
    config = WebFlowConfig(driver_path="", base_url="u", tool_version="t", routing="r")
    service.create_jobs([{"part_number": "P1"}], config, seen.append)
    assert seen == ["Starting the browser..."]


class _LinkSheet:
    def __init__(self, path):
        self.written = None
        self.closed = False

    def open(self):
        pass

    def close(self):
        self.closed = True

    def write_webflow_links(self, links, save=True):
        _LinkSheet.last = links
        return len(links)


class _FlowWithUrl(FakeWebFlow):
    def create_and_fill_jobs(self, variants, tool_version, routing, progress=None):
        return [{"PartNumber": v["part_number"], "JobId": "7", "Url": "http://x/app/ShowJob/7"} for v in variants]


def test_create_jobs_writes_links_to_the_master_sheet():
    service = WebFlowJobService(_FlowWithUrl, _LinkSheet)
    config = WebFlowConfig(driver_path="", base_url="u", tool_version="t", routing="r")
    results = service.create_jobs([{"part_number": "P1"}], config, master_sheet_path="m.xlsx")
    assert _LinkSheet.last == {"P1": "http://x/app/ShowJob/7"}
    assert "LinkError" not in results[0]


def test_create_jobs_reports_a_sheet_without_a_link_column():
    class NoLinks(_LinkSheet):
        write_webflow_links = None

    service = WebFlowJobService(_FlowWithUrl, NoLinks)
    config = WebFlowConfig(driver_path="", base_url="u", tool_version="t", routing="r")
    results = service.create_jobs([{"part_number": "P1"}], config, master_sheet_path="m.xlsx")
    assert "no WebFlow link column" in results[0]["LinkError"]


def test_webflow_link_text_is_wf_plus_the_job_number():
    from autohub.core.webflow_links import is_link, webflow_link_text

    assert webflow_link_text("https://h:8881/app/ShowJob/16406") == "WF16406"
    assert webflow_link_text("https://h:8881/app/ShowJob/16406/") == "WF16406"
    assert webflow_link_text("nothing") == ""
    assert is_link("https://x") and not is_link("WF218076")
