import shutil
import zipfile

import openpyxl

from autohub.services.common.read_only_flag import clear_read_only_recommended, has_read_only_recommended

SAMPLE = "datas/mastersheet/Honda_GDI_container_release_info_latest.xlsx"
MG1 = "datas/mastersheet/Honda_6SAY_Container_MasterSheet_r00.xlsx"


def _flagged_copy(tmp_path):
    copy = tmp_path / "a.xlsx"
    with zipfile.ZipFile(SAMPLE) as source, zipfile.ZipFile(copy, "w", zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "xl/workbook.xml" and b"readOnlyRecommended" not in data:
                data = data.replace(b"<sheets>", b'<fileSharing readOnlyRecommended="1"/><sheets>', 1)
            target.writestr(item, data)
    return copy


def test_flag_is_removed_and_the_workbook_still_opens(tmp_path):
    copy = _flagged_copy(tmp_path)
    assert has_read_only_recommended(str(copy))
    assert clear_read_only_recommended(str(copy))
    assert not has_read_only_recommended(str(copy))
    with zipfile.ZipFile(SAMPLE) as before, zipfile.ZipFile(copy) as after:
        assert sorted(before.namelist()) == sorted(after.namelist())
        assert b"readOnlyRecommended" not in after.read("xl/workbook.xml")
    assert openpyxl.load_workbook(copy, read_only=True).sheetnames[0] == "ECU Container Release Honda GDI"
    assert not clear_read_only_recommended(str(copy))


def test_files_without_the_flag_are_untouched(tmp_path):
    copy = tmp_path / "b.xlsx"
    shutil.copy(MG1, copy)
    before = copy.read_bytes()
    assert not clear_read_only_recommended(str(copy))
    assert copy.read_bytes() == before
