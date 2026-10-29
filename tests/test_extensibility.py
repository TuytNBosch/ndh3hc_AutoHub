"""Open/Closed: new behaviour is added by registering, not by editing (OCP-1, OCP-2)."""
from autohub.services.common.header_rules import HeaderRule, map_headers
from autohub.services.common.sheet_grid import SheetGrid
from autohub.services.EcuInfoSheet.parser import HEADER_RULES
from autohub.services.HWInfo.HWInfo import HWInfo
from autohub.services.HWInfo.sources import HWSourceRegistry, default_registry


class _StubSource:
    def read(self, path, password):
        return [
            {
                "part_number": "37820-AAA-B100-M6",
                "source": "stub",
                "hw_ident": "0261S00000",
                "b_number": "",
                "customer_order": "",
                "field15": "",
                "eu_mark": "",
                "ss_id": "",
                "remark": "",
            }
        ]


def test_a_new_hw_file_type_needs_only_a_registration(tmp_path):
    path = tmp_path / "list.pdf"
    path.write_bytes(b"%PDF")
    assert HWInfo(str(path)).load_data() is False  # unknown until registered

    registry = default_registry()
    registry.register(".pdf", _StubSource())
    hw = HWInfo(str(path), registry=registry)
    assert hw.load_data() is True
    assert hw.find("37820-AAA-B100-M6")["hw_ident"] == "0261S00000"


def test_unsupported_message_lists_the_registered_types(tmp_path):
    path = tmp_path / "x.txt"
    path.write_text("x")
    registry = HWSourceRegistry()
    registry.register(".abc", _StubSource())
    hw = HWInfo(str(path), registry=registry)
    assert not hw.load_data()
    assert ".abc" in hw.last_error


def _grid(*cells):
    return SheetGrid([list(cells)])


def test_a_new_ecu_column_is_one_rule():
    grid = _grid("Event", "MP No.", "PART NO.", "Brand New Column")
    extra = [*HEADER_RULES, HeaderRule(r"brand new column", "ecu", "BrandNew")]
    columns = map_headers(grid, 1, extra)
    assert columns["ecu"]["BrandNew"] == 4
    assert "BrandNew" not in map_headers(grid, 1, HEADER_RULES).get("ecu", {})


def test_repeated_headers_are_assigned_by_occurrence():
    grid = _grid("MP No.", "MP No.", "MP No.")
    columns = map_headers(grid, 1, HEADER_RULES)
    assert (columns["ecu"]["MP"], columns["main"]["MP"], columns["boot"]["MP"]) == (1, 2, 3)


def test_group_references_map_several_headers_to_different_fields():
    grid = _grid("Security Type Ⅰ SK1 ELS2", "Security Type Ⅰ SK2 ELS2", "Security Type Ⅰ SK3 ELS2")
    assert map_headers(grid, 1, HEADER_RULES)["boot"] == {"SK1": 1, "SK2": 2, "SK3": 3}
