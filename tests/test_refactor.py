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
