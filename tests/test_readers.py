"""Readers must load every layout in datas/ (parsers run on openpyxl, so no Excel is needed)."""
import io
import warnings
import zipfile
from functools import lru_cache
from pathlib import Path

import msoffcrypto
import openpyxl
import pytest

from autohub.services.common.sheet_grid import LayoutError, SheetGrid
from autohub.services.EcuInfoSheet.parser import parse_ecu_info
from autohub.services.HWInfo.HWInfo import HWInfo
from autohub.services.HWInfo.parser import parse_body_table
from autohub.services.SystemMatrix.parser import is_system_matrix_sheet, parse_system_matrix

DATAS = Path(__file__).resolve().parent.parent / "datas"
pytestmark = pytest.mark.skipif(not DATAS.is_dir(), reason="sample data folder not available")


@lru_cache(maxsize=None)
def _embedded_workbook(path: str):
    buffer = io.BytesIO()
    with open(path, "rb") as f:
        office_file = msoffcrypto.OfficeFile(f)
        office_file.load_key(password="hondabosch")
        office_file.decrypt(buffer)
    archive = zipfile.ZipFile(buffer)
    name = next(n for n in archive.namelist() if "embeddings/" in n)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return openpyxl.load_workbook(io.BytesIO(archive.read(name)), data_only=True, keep_vba=name.endswith(".xlsm"))


def _ecu_info(name: str) -> dict:
    sheet = _embedded_workbook(str(DATAS / "EcuInfoSheet" / name))["Factory_event"]
    return parse_ecu_info(SheetGrid.from_openpyxl(sheet))


def _system_matrix(name: str) -> dict:
    workbook = _embedded_workbook(str(DATAS / "SystemMatrix" / name))
    sheet = next(ws for ws in workbook.worksheets if is_system_matrix_sheet(ws.title))
    return parse_system_matrix(SheetGrid.from_openpyxl(sheet))


@pytest.mark.parametrize(
    "name, event, mp, project",
    [
        ("CR-GDI-HG27B-SY010-3.xlsx", "DAN", "MP1", "62XS"),
        ("CR-PFI-HG28A-SY012-1.xlsx", "DAN", "MP1", "6SAY"),
    ],
)
def test_ecu_info_62xs_style(name, event, mp, project):
    info = _ecu_info(name)
    assert info["GeneralInfo"][0]["Project"] == project
    assert len(info["Main"]) == len(info["Container"]) == len(info["Boot"]) == 6
    assert [(g["Event"], g["MP"], len(g["Rows"])) for g in info["Ecu"]] == [(event, mp, 6)]
    assert info["Main"][0]["NumCompID"].replace(" ", "").startswith("37820-")
    assert info["Main"][0]["CALIBID"] == info["Main"][0]["NumProgID"]


def test_ecu_info_with_shifted_columns_and_several_mp_groups():
    info = _ecu_info("CR-GDI-HGMI01-SY007-0.xlsx")
    assert len(info["Main"]) == 4
    assert [(g["MP"], len(g["Rows"])) for g in info["Ecu"]] == [("MP4", 2), ("MP6", 2)]
    first = info["Main"][0]
    assert first["NumCompID"] == "37820-5BF-U140-M6"
    assert first["NumProgID"] == "37805-5BF-U140"
    assert first["NumReWrecuid"] == "30-19-05-00-00"
    assert float(info["Boot"][0]["SK1"]) == 3670  # the legacy fixed columns read this as the rewrite id
    assert info["Container"][0]["Destination"] == "KU"


def test_ecu_info_rejects_a_system_matrix():
    workbook = _embedded_workbook(str(DATAS / "SystemMatrix" / "CR-GDI-HGMI01-SY004-2.xlsx"))
    for sheet in workbook.worksheets:
        with pytest.raises(LayoutError):
            parse_ecu_info(SheetGrid.from_openpyxl(sheet))


@pytest.mark.parametrize(
    "name, variants, hardware, first_ssid, first_mark",
    [
        ("CR-GDI-HG27B-SY009-4.xlsx", 6, "MG1CS022", "41X", "7C8"),
        ("CR-PFI-HG28A-SY007-2.xlsx", 6, "MG1CA020", "UDP", "QPR"),
    ],
)
def test_system_matrix_with_hardware_type(name, variants, hardware, first_ssid, first_mark):
    matrix = _system_matrix(name)
    assert len(matrix["GeneralInfo"]) == len(matrix["FormB"]) == len(matrix["Setting"]) == variants
    assert {item["Hardware"] for item in matrix["FormB"]} == {hardware}  # "MG1 CA020" is normalised
    assert matrix["FormB"][0]["SSID"] == first_ssid
    assert matrix["FormB"][0]["ECUMARK"] == first_mark


def test_system_matrix_settings_and_japanese_labels():
    matrix = _system_matrix("CR-GDI-HG27B-SY009-4.xlsx")
    assert matrix["Setting"][0]["Displacement"] == "1.5L"
    assert matrix["Setting"][0]["Transmission"] == "CVT"
    assert matrix["GeneralInfo"][0]["Destination"] == "M"  # row labelled 仕向け only


def test_system_matrix_variant_columns_may_have_gaps():
    matrix = _system_matrix("CR-GDI-HGMI01-SY006-0.xlsx")
    columns = [item["Column"] for item in matrix["GeneralInfo"]]
    assert len(columns) == 10
    assert "J" in columns and "I" not in columns and "L" not in columns
    assert all(item["Hardware"] is None for item in matrix["FormB"])  # this series leaves HARD TYPE blank


def test_system_matrix_flags_abolished_columns():
    matrix = _system_matrix("CR-GDI-HGMI01-SY004-2.xlsx")
    assert len(matrix["GeneralInfo"]) == 17
    assert [item["Column"] for item in matrix["GeneralInfo"] if item["Abolished"]] == ["G", "O", "U"]


@pytest.mark.parametrize(
    "name, parts",
    [
        ("tl_r01_62XS_MP1_ECU_PN_V01.xlsx", 6),
        ("tl_r01_MG1CA020_6SAY_MP1_ECU_PN_V01.xlsx", 6),
        ("RE [Honda - 62XS][Container] Information needed for MP1 container generation.eml", 6),
        ("RE_ [Honda - 62XS][Container] Information needed for MP2 container generation.eml", 12),
        ("RE [Honda][5BFT-P0369][Container] Information needed for group 2 container generation.eml", 12),
        ("RE [Honda][P0369-5BFW][Container] Information needed for container generation.eml", 4),
        ("RE HondaP0369-5BFYContainer Information needed for container generation.msg", 2),
    ],
)
def test_hw_info_sources(name, parts):
    hw = HWInfo(str(DATAS / "HWInfo" / name))
    assert hw.load_data(), hw.last_error
    assert len(hw.records) == parts
    assert all(r["hw_ident"] for r in hw.records)


def test_hw_info_email_prefers_workbook_attachment_over_body():
    hw = HWInfo(str(DATAS / "HWInfo" / "RE [Honda - 62XS][Container] Information needed for MP1 container generation.eml"))
    assert hw.load_data()
    record = hw.find("37820-62X -MD10-M6")
    assert (record["hw_ident"], record["b_number"]) == ("0261S10A2Y", "0261B00CE7-00")
    assert not any("62XS-" in r["part_number"] for r in hw.records)  # quoted old numbers carry no HW data


def test_hw_info_mp2_email_includes_both_attached_sheets():
    hw = HWInfo(str(DATAS / "HWInfo" / "RE_ [Honda - 62XS][Container] Information needed for MP2 container generation.eml"))
    assert hw.load_data()
    assert hw.find("37820-62X-MD20-M6")["hw_ident"] == "0261S10BC0"  # MP2 sheet
    assert hw.find("37820-62X-MD10-M6")["hw_ident"] == "0261S10A2Y"  # older MP1 sheet in the same workbook


def test_hw_info_msg_body_table():
    hw = HWInfo(str(DATAS / "HWInfo" / "RE HondaP0369-5BFYContainer Information needed for container generation.msg"))
    assert hw.load_data()
    record = hw.find("37820-5BF-G160-M6")
    assert (record["hw_ident"], record["b_number"], record["eu_mark"], record["ss_id"]) == (
        "0261S10C2F",
        "0261B00E52-00",
        "JMY",
        "JMY",
    )


def test_hw_info_rejects_unsupported_file(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("not a hw file")
    hw = HWInfo(str(path))
    assert not hw.load_data()
    assert ".txt" in hw.last_error


def test_body_table_ignores_lines_without_hw_data():
    text = "1\t5BF-G160\tKG\t\t\t37820-5BF-G160-M6\t37820-5BF-G16\tJMY\tJMY\n==> 37820-62XS-M*10-M6 changes"
    records = parse_body_table(text, "mail")
    assert [(r["part_number"], r["eu_mark"], r["ss_id"]) for r in records] == [("37820-5BF-G160-M6", "JMY", "JMY")]
