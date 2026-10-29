"""Home workflows through the presenter and service, with fakes instead of Excel, Qt dialogs and threads."""
from autohub.modules.home.presenter import HomePresenter
from tests.fakes import (
    FakeDialogs,
    FakeDocument,
    FakeMasterSheet,
    FakeView,
    MemorySettings,
    build_service,
    run_inline,
)


def _presenter(tmp_path, service, dialogs=None, view=None, settings=None):
    master = tmp_path / "master.xlsx"
    master.write_bytes(b"x")
    settings = settings or MemorySettings({"master_sheet_path": str(master)})
    view = view or FakeView()
    dialogs = dialogs or FakeDialogs()
    presenter = HomePresenter(view, service, settings, dialogs, run_inline)
    presenter.restore_saved_paths()
    return presenter, view, dialogs, settings


def test_restore_saved_paths_shows_the_master_sheet_name(tmp_path):
    _, view, _, _ = _presenter(tmp_path, build_service())
    assert view.file_names["Master Sheet"].endswith("master.xlsx")


def test_new_variant_enables_update_without_editing(tmp_path):
    master = FakeMasterSheet(new_rows=[{"J": "37820-62X-MD10-M6"}])
    dialogs = FakeDialogs(files=["ecu.xlsx", "matrix.xlsx"])
    presenter, view, _, _ = _presenter(tmp_path, build_service(master=master), dialogs)

    presenter.new_variant()

    assert view.rows == [{"J": "37820-62X-MD10-M6"}]
    assert view.states["update"] == (True, "Update Master Sheet")
    assert view.states["new"] == (True, "New variant")
    assert dialogs.picked == ["Select ECU Info Sheet CR file", "Select System Matrix CR file"]


def test_new_variant_with_nothing_new_keeps_update_disabled(tmp_path):
    presenter, view, dialogs, _ = _presenter(
        tmp_path, build_service(master=FakeMasterSheet(new_rows=[])), FakeDialogs(files=["e.xlsx", "m.xlsx"])
    )
    presenter.new_variant()
    assert view.states["update"][0] is False
    assert "No new variants" in dialogs.infos[-1][1]


def test_new_variant_passes_hw_info_to_the_master_sheet(tmp_path):
    master = FakeMasterSheet(new_rows=[{"J": "P"}])
    dialogs = FakeDialogs(files=["e.xlsx", "m.xlsx", "hw.eml"], hw_answer=True)
    presenter, _, _, settings = _presenter(tmp_path, build_service(master=master), dialogs)

    presenter.new_variant()

    assert master.compute_args[2] is not None
    assert settings.data["hw_info_path"] == "hw.eml"


def test_new_variant_stops_when_a_file_dialog_is_cancelled(tmp_path):
    master = FakeMasterSheet()
    presenter, view, _, _ = _presenter(tmp_path, build_service(master=master), FakeDialogs(files=["e.xlsx"]))
    presenter.new_variant()
    assert master.compute_args is None
    assert "new" not in view.states


def test_new_variant_reports_the_reader_error(tmp_path):
    matrix = FakeDocument(ok=False, error="'m.xlsx' is not a readable System Matrix: no part numbers")
    presenter, view, dialogs, _ = _presenter(
        tmp_path, build_service(matrix=matrix), FakeDialogs(files=["e.xlsx", "m.xlsx"])
    )
    presenter.new_variant()
    assert dialogs.errors == [("New variant", "'m.xlsx' is not a readable System Matrix: no part numbers")]
    assert view.states["new"] == (True, "New variant")


def test_documents_are_closed_even_when_loading_fails(tmp_path):
    ecu = FakeDocument(ok=False, error="bad", ecu_info={})
    master = FakeMasterSheet()
    matrix = FakeDocument(system_info={})
    presenter, _, _, _ = _presenter(
        tmp_path, build_service(master=master, ecu=ecu, matrix=matrix), FakeDialogs(files=["e.xlsx", "m.xlsx"])
    )
    presenter.new_variant()
    assert ecu.closed and master.closed and matrix.closed


def test_update_saves_the_table_rows_and_publishes_webflow_variants(tmp_path):
    master = FakeMasterSheet(rows=[{"_row": 11, "J": "P"}], webflow=[{"part_number": "P"}])
    presenter, view, dialogs, _ = _presenter(tmp_path, build_service(master=master))
    view.rows = [{"_row": None, "J": "P"}]

    presenter.update_master_sheet()

    assert master.saved == [{"_row": None, "J": "P"}]
    assert view.rows == [{"_row": 11, "J": "P"}]
    assert view.published == [[{"part_number": "P"}]]
    assert view.states["update"] == (False, "Update Master Sheet")
    assert "Updated 1 variant" in dialogs.infos[-1][1]


def test_update_without_rows_does_nothing(tmp_path):
    master = FakeMasterSheet()
    presenter, _, _, _ = _presenter(tmp_path, build_service(master=master))
    presenter.update_master_sheet()
    assert master.saved is None


def test_update_requires_a_valid_master_sheet(tmp_path):
    view = FakeView()
    view.rows = [{"J": "P"}]
    presenter, _, dialogs, _ = _presenter(tmp_path, build_service(), view=view, settings=MemorySettings())
    presenter.update_master_sheet()
    assert dialogs.errors == [("Update variants", "Select a valid Master Sheet file.")]


def test_load_shows_rows_and_keeps_update_disabled(tmp_path):
    master = FakeMasterSheet(rows=[{"_row": 11}, {"_row": 14}], webflow=[{"part_number": "P"}])
    presenter, view, dialogs, _ = _presenter(tmp_path, build_service(master=master))

    presenter.load_variants()

    assert len(view.rows) == 2
    assert view.states["update"][0] is False
    assert view.states["clear"] is True
    assert view.states["load"] == (True, "Load variants")
    assert view.published == [[{"part_number": "P"}]]
    assert "Loaded 2 variants" in dialogs.infos[-1][1]


def test_clear_resets_the_table_and_buttons(tmp_path):
    presenter, view, _, _ = _presenter(tmp_path, build_service(master=FakeMasterSheet(rows=[{"_row": 11}])))
    presenter.load_variants()
    presenter.clear_table()
    assert view.rows == []
    assert view.states["clear"] is False and view.states["update"][0] is False


def test_editing_the_table_enables_update(tmp_path):
    presenter, view, _, _ = _presenter(tmp_path, build_service())
    presenter.on_table_edited()
    assert view.states["update"] == (True, "Update Master Sheet")


def test_load_and_new_variant_report_their_steps_in_the_progress_window(tmp_path):
    master = FakeMasterSheet(rows=[{"J": "a"}], new_rows=[])
    dialogs = FakeDialogs(files=["e.xlsx", "m.xlsx"])
    presenter, _, _, _ = _presenter(tmp_path, build_service(master=master), dialogs)

    presenter.load_variants()
    presenter.new_variant()

    load, new = dialogs.windows
    assert load.title == "Load variants" and load.steps == ["Opening the Master Sheet...", "Reading the variants..."]
    assert new.title == "New variant" and "Reading the System Matrix..." in new.steps
    assert dialogs.infos[0][1] == "Loaded 1 variant from the Master Sheet."
