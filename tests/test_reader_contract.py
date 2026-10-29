"""One contract for every document reader (LSP-1, LSP-2): load_data() -> bool and last_error explains a failure."""
import pytest

from autohub.core.records import DocumentReader
from autohub.services.EcuInfoSheet.EcuInfoSheet import EcuInfoSheet
from autohub.services.HWInfo.HWInfo import HWInfo
from autohub.services.KickOff.KickOff import KickOffMeeting
from autohub.services.SystemMatrix.SystemMatrix import SystemMatrix
from tests.fakes import FakeDocument


def _unreadable(tmp_path):
    path = tmp_path / "broken.xlsx"
    path.write_bytes(b"this is not a workbook")
    return str(path)


@pytest.mark.parametrize("reader_class", [EcuInfoSheet, SystemMatrix])
def test_excel_readers_report_a_failed_open_instead_of_raising(reader_class, tmp_path):
    reader = reader_class(_unreadable(tmp_path))
    reader.open()  # must not raise
    assert reader.load_data() is False
    assert reader.last_error


def test_hw_info_reports_unreadable_and_unsupported_files(tmp_path):
    broken = HWInfo(_unreadable(tmp_path))
    assert broken.load_data() is False and broken.last_error

    other = tmp_path / "notes.txt"
    other.write_text("x")
    unsupported = HWInfo(str(other))
    assert unsupported.load_data() is False and ".txt" in unsupported.last_error


def test_kick_off_reports_an_unreadable_file_instead_of_raising(tmp_path):
    reader = KickOffMeeting(_unreadable(tmp_path))
    assert reader.load_data() is False and reader.last_error


def test_readers_and_fakes_satisfy_the_same_protocol(tmp_path):
    readers = [EcuInfoSheet("x"), SystemMatrix("x"), HWInfo("x"), KickOffMeeting("x"), FakeDocument()]
    for reader in readers:
        assert hasattr(reader, "load_data") and hasattr(reader, "last_error")
    # runtime check of the structural type
    assert all(isinstance(r.last_error, str) for r in readers)
    _: list[DocumentReader] = readers  # noqa: F841  (static conformance for type checkers)


def test_master_sheet_open_failure_raises_before_anything_can_be_written(tmp_path):
    from autohub.services.MasterSheet.MasterSheet import MasterSheet

    sheet = MasterSheet(_unreadable(tmp_path))
    with pytest.raises(RuntimeError, match="Error opening Excel file"):
        sheet.open()
