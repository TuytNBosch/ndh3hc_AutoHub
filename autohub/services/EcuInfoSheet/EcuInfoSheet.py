from autohub.services.common.sheet_grid import SheetGrid, normalize
from autohub.services.common.workbook import ExcelDocument
from autohub.services.EcuInfoSheet.parser import SHEET_NAME, parse_ecu_info, parse_engine_family


class EcuInfoSheet(ExcelDocument):
    document_name = "ECU Info Sheet"

    def __init__(self, file_path: str, password: str = "hondabosch", quit: bool = False):
        super().__init__(file_path, password, quit)
        self.ecu_info = {"GeneralInfo": [], "Ecu": [], "Container": [], "Main": [], "Boot": []}

    def load_data(self) -> bool:
        info = self._parse(lambda name: normalize(name) == SHEET_NAME, parse_ecu_info)
        if info is None:
            return False
        engine_family = self._read_engine_family()
        if engine_family:
            for general in info.get("GeneralInfo", []):
                general["EngineFamily"] = engine_family
        self.ecu_info = info
        return True

    def _read_engine_family(self) -> str:
        """Engine family from the workbook's "Issue CR" sheet; blank when there is none."""
        for sheet in self.workbook.Worksheets:
            try:
                return parse_engine_family(SheetGrid.from_com(sheet))
            except Exception:
                continue
        return ""
