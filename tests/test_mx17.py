import openpyxl
import pytest

from autohub.services.MasterSheet import mx17_layout as layout
from autohub.services.MasterSheet.master_sheet_factory import open_master_sheet, workbook_sheet_names
from autohub.services.MasterSheet.MasterSheet import MasterSheet
from autohub.services.MasterSheet.mx17_sheet import Mx17MasterSheet

MX17 = "datas/mastersheet/Honda_GDI_container_release_info_latest.xlsx"
MG1 = "datas/mastersheet/Honda_6SAY_Container_MasterSheet_r00.xlsx"


def test_factory_picks_layout_by_sheet_names():
    assert layout.is_mx17_sheet_names(workbook_sheet_names(MX17))
    assert not layout.is_mx17_sheet_names(workbook_sheet_names(MG1))
    assert workbook_sheet_names("missing.xlsx") == []


def test_factory_returns_expected_classes():
    assert type(open_master_sheet(MX17)) is Mx17MasterSheet
    assert type(open_master_sheet(MG1)) is MasterSheet


def test_main_row_round_trips_part_number():
    ws = openpyxl.load_workbook(MX17, data_only=True)[layout.MAIN_SHEET_NAME]
    row = {c.column_letter: c.value for c in ws[748]}
    home = layout.home_from_main(row)
    assert home["J"] == row["W"]
    assert layout.main_values_from_home(home)[layout.PART_NUMBER_COLUMN] == row["W"]


def test_info_sheet_name_is_safe():
    assert layout.info_sheet_name("5BFW") == "5BFW_Info"
    name = layout.info_sheet_name("a/b:" + "x" * 50)
    assert len(name) <= 31 and "/" not in name and ":" not in name


def test_new_main_values_sets_project_and_date():
    from datetime import datetime
    values = layout.new_main_values({"J": "37820-5BF-G26"}, datetime(2025, 1, 2))
    assert values["C"] == "HONDA GDI" and values["W"] == "37820-5BF-G26"
